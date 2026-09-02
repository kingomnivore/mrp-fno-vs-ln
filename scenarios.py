"""Five business cases, every lot-sizing rule run in each, scored by category.

Each case fixes a lead time, a forecast error and the part of the item
population it draws from. Scores are normalised within a case, so they rank
rules for that business and are not comparable across cases.

No coverage time fence is applied inside a business case. The fence is studied
on its own in fence.py; here it must not bind on any rule.
"""
import numpy as np
import pandas as pd

import config as C
import data as D
import rolling as R

CATEGORIES = {
    "Service": ("fill", False),               # higher is better
    "Working capital": ("cover_days", True),  # lower is better
    "Planner workload": ("orders_per_year", True),
}


def configs():
    """Every lot-sizing rule, tagged with which product documents it.

    Corrected after checking Infor's own manuals. Two earlier entries were
    removed because they modelled something LN does not do:

      - a calendar-anchored plan period, treated as an LN lot-sizing rule. It
        is not. LN's time-based grouping is the ORDER INTERVAL, "measured
        starting at the last generated order", which floats with demand
        exactly as F&O's Period coverage code does. There is no anchored
        alternative for F&O to be missing.
      - a plan period of varying length, treated the same way. Plan periods
        are the buckets an item master plan is recorded in, not a lot-sizing
        rule, and LN spreads a period's quantity across its days in
        proportion to capacity rather than placing it at a point.

    What is left is a real asymmetry in both directions. LN documents Fixed
    Order Quantity and Economic Order Quantity as order methods; F&O has no
    coverage code for either. F&O documents Priority and Decoupling point;
    no LN equivalent was established.
    """
    c = [{"name": "Requirement / Lot-for-Lot", "kind": "l4l", "L": 1,
          "who": "Both"}]
    for L in C.PERIODS:
        c.append({"name": f"Period / Order interval {L}d", "kind": "float",
                  "L": L, "who": "Both"})
    c.append({"name": "Min-Max / Replenish to max", "kind": "minmax", "L": 1,
              "who": "Both"})
    for days in C.FOQ_DAYS:
        c.append({"name": f"Fixed order qty {days}d", "kind": "foq",
                  "days": days, "L": days, "who": "LN only"})
    for ratio in C.EOQ_RATIOS:
        c.append({"name": f"EOQ ratio {ratio:g}", "kind": "eoq",
                  "setup": float(ratio), "hold": 1.0, "L": 1, "who": "LN only"})
    return c


def score(series, lower_is_better):
    """Normalise to 0-100 within a case. 100 is the best achieved there."""
    lo, hi = float(series.min()), float(series.max())
    if hi - lo < 1e-12:
        return pd.Series(100.0, index=series.index)
    s = (series - lo) / (hi - lo)
    return 100.0 * (1.0 - s if lower_is_better else s)


def run(daily, profile, log=print):
    """Returns (raw rows, scored table, category spreads)."""
    pool = D.sample(profile, daily)
    cfgs = configs()
    rows = []
    for case, spec in C.CASES.items():
        items = pool if spec["classes"] is None else \
            pool[pool["quadrant"].isin(spec["classes"])]
        sc = {"lead_time": spec["lead_time"], "replan_every": C.REPLAN_EVERY,
              "visibility": C.VISIBILITY_DAYS, "noise": spec["noise"],
              "opening_stock_days": C.OPENING_STOCK_DAYS,
              "coverage_fence": None}
        for _, it in items.iterrows():
            a = D.series(daily, it["StockCode"])
            md = float(a.mean())
            for base in cfgs:
                cfg = dict(base)
                if cfg["kind"] == "minmax":
                    # The minimum must cover the lead time, or the rule cannot
                    # serve demand and is a strawman. An earlier version fixed
                    # it at 7 and 28 days of mean demand regardless of lead
                    # time, which returned 65.8% fill at a 60-day lead time.
                    lt = spec["lead_time"]
                    cfg["mn"], cfg["mx"] = lt * md, (lt + 28) * md
                if cfg["kind"] == "foq":
                    cfg["Q"] = max(cfg["days"] * md, 1.0)
                m = R.simulate(a, cfg, sc,
                               seed=R.stable_seed(it["StockCode"], cfg["name"], case))
                rows.append({"case": case, "config": cfg["name"],
                             "who": cfg["who"], **m})
        log(f"  {case}: {len(items)} items x {len(cfgs)} rules")

    raw = pd.DataFrame(rows)
    agg = raw.groupby(["case", "config", "who"], as_index=False).agg(
        fill=("fill", "mean"), cover_days=("cover_days", "mean"),
        orders_per_year=("orders_per_year", "mean"))

    # A category may only rank rules where the underlying outcome actually
    # differs. Normalising a spread of 0.0003 in fill rate onto a 0-100 scale
    # manufactures a ranking out of nothing.
    out, spreads = [], []
    for case in C.CASES:
        sub = agg[agg["case"] == case].copy()
        ranked = []
        for cat, (col, lower) in CATEGORIES.items():
            if col == "fill":
                spread = 100 * float(sub[col].max() - sub[col].min())
            else:
                spread = 100 * float(sub[col].max() - sub[col].min()) / float(sub[col].mean())
            ok = spread >= C.MIN_SPREAD[cat]
            spreads.append({"case": case, "category": cat, "spread": spread,
                            "ranked": ok})
            sub[cat] = score(sub[col], lower) if ok else np.nan
            if ok:
                ranked.append(cat)
        sub["Balanced"] = sub[ranked].mean(axis=1)
        out.append(sub)
    return raw, pd.concat(out, ignore_index=True), pd.DataFrame(spreads)


def winners(scored):
    """Top rule per category, with the margin over second place."""
    rows = []
    for case in C.CASES:
        sub = scored[scored["case"] == case]
        row = {"case": case}
        for cat in list(CATEGORIES) + ["Balanced"]:
            row[cat] = "not ranked" if sub[cat].isna().all() \
                else sub.loc[sub[cat].idxmax(), "config"]
        top = sub.sort_values("Balanced", ascending=False)
        row["margin"] = float(top.iloc[0]["Balanced"] - top.iloc[1]["Balanced"])
        row["verdict"] = "clear" if row["margin"] >= C.TIE_MARGIN else "tie"
        row["who"] = top.iloc[0]["who"]
        rows.append(row)
    return pd.DataFrame(rows)


def time_phased_service(scored):
    """Service spread once the reorder-point rule is set aside.

    Replenish-to-maximum belongs to a different class and dominates the raw
    spread, so the article reports both figures rather than one.
    """
    tp = scored[~scored["config"].str.startswith("Min-Max")]
    return {case: 100 * float(tp[tp["case"] == case]["fill"].max()
                              - tp[tp["case"] == case]["fill"].min())
            for case in C.CASES}
