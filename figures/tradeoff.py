"""Purchase orders against stock held, with each documented rule family plotted.

The floating window traces the lower edge of the trade. Neither method only
LN documents reaches inside it, which is the article's central negative result.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config as C
import data as D
import rolling as R
import style as S

NAME = "fig_tradeoff.png"
BASE = {"lead_time": 5, "replan_every": C.REPLAN_EVERY,
        "visibility": C.VISIBILITY_DAYS, "noise": C.BASE_SIGMA,
        "opening_stock_days": C.OPENING_STOCK_DAYS}


def data(daily, profile):
    """One row per item and rule, at a common short lead time."""
    items = D.sample(profile, daily)
    rows = []
    for _, it in items.iterrows():
        a = D.series(daily, it["StockCode"])
        md = float(a.mean())
        for L in C.PERIODS:
            cfg = {"name": f"Window {L}d", "kind": "float", "L": L}
            rows.append({"family": "Floating window (both)", "L": L,
                         **R.simulate(a, cfg, BASE,
                                      R.stable_seed(it["StockCode"], cfg["name"]))})
        for days in C.FOQ_DAYS:
            cfg = {"name": f"FOQ {days}d", "kind": "foq", "Q": max(days * md, 1.0)}
            rows.append({"family": "Fixed order quantity (LN)", "L": days,
                         **R.simulate(a, cfg, BASE,
                                      R.stable_seed(it["StockCode"], cfg["name"]))})
        for ratio in C.EOQ_RATIOS:
            cfg = {"name": f"EOQ {ratio}", "kind": "eoq",
                   "setup": float(ratio), "hold": 1.0}
            rows.append({"family": "Economic order quantity (LN)", "L": ratio,
                         **R.simulate(a, cfg, BASE,
                                      R.stable_seed(it["StockCode"], cfg["name"]))})
    return pd.DataFrame(rows)


def elasticities(tr):
    """Per cent change per doubling of the window length."""
    w = tr[tr["family"].str.startswith("Floating")]
    # log2 needs strictly positive inputs, and both regressions must run on the
    # same rows or the two elasticities are not comparable with each other.
    # An item that never ordered, or held no stock at all, is dropped from both.
    d = w[(w["orders_per_year"] > 0) & (w["cover_days"] > 0)]
    X = np.column_stack([np.ones(len(d)), np.log2(d["L"])])
    out = {}
    for target, label in [("orders_per_year", "purchase orders"),
                          ("cover_days", "days of cover")]:
        beta = np.linalg.lstsq(X, np.log2(d[target]), rcond=None)[0]
        out[label] = 100 * (2 ** beta[1] - 1)
    out["_n"] = len(d)
    return out


def render(tr):
    g = tr.groupby(["family", "L"]).agg(cover=("cover_days", "mean"),
                                        orders=("orders_per_year", "mean")).reset_index()
    fig, ax = plt.subplots(figsize=(8.8, 5.2))
    spec = [("Floating window (both)", S.C_FNO, "-o",
             "Floating window: F&O Period, LN order interval"),
            ("Fixed order quantity (LN)", S.C_LN, "--s",
             "Fixed order quantity: LN only"),
            ("Economic order quantity (LN)", S.C_WARN, ":^",
             "Economic order quantity: LN only")]
    for fam, col, mk, lab in spec:
        sub = g[g["family"] == fam].sort_values("cover")
        ax.plot(sub["cover"], sub["orders"], mk, color=col, lw=1.8, ms=7, label=lab)
        if fam.startswith("Floating"):
            for _, r in sub.iterrows():
                ax.annotate(f"{int(r['L'])}d", (r["cover"], r["orders"]),
                            textcoords="offset points", xytext=(7, 6),
                            fontsize=9, color=col, fontweight="semibold")
    ax.set_xlabel("Average stock held (days of cover)")
    ax.set_ylabel("Purchase orders raised per item per year")
    ax.set_title("Purchase orders against stock held", fontsize=12, pad=14)
    ax.legend(loc="upper right", fontsize=9)
    S.clean(ax)
    fig.tight_layout()
    fig.savefig(NAME, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return NAME
