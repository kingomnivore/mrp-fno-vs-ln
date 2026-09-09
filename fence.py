"""What a coverage time fence shorter than the lead time costs.

F&O excludes demand beyond the fence outright: "The system doesn't generate
requirement transactions for any supply and demand that falls outside the
coverage time fence." This measures the price of that exclusion, and locates
where service comes back.

Two sweeps, because the first one misled. A coarse grid at a single window
length suggested the recovery arrived a full window above the lead time. A
fine sweep across four window lengths shows the four curves are
indistinguishable through the transition, so the window length does not
govern it and the lead time does.
"""
import numpy as np
import pandas as pd

import config as C
import data as D
import rolling as R


def grid(daily, profile, log=print):
    """Coarse lead time by fence grid, at one window length."""
    items = D.sample(profile, daily).sample(
        min(C.FENCE_ITEMS, 4 * C.PER_QUADRANT), random_state=C.SAMPLE_SEED)
    cfg = {"name": f"Window {C.FENCE_PERIOD}d", "kind": "float",
           "L": C.FENCE_PERIOD}
    base = {"replan_every": C.REPLAN_EVERY, "visibility": C.VISIBILITY_DAYS,
            "noise": C.BASE_SIGMA, "opening_stock_days": C.OPENING_STOCK_DAYS}
    rows = []
    for lt in C.FENCE_LEADS:
        for fence in C.FENCE_VALUES:
            for c in items["StockCode"]:
                m = R.simulate(D.series(daily, c), cfg,
                               dict(base, lead_time=lt, coverage_fence=fence),
                               seed=R.stable_seed(c, lt, fence))
                # One row per item, not per grid cell. Regressing on the 49
                # aggregated cells throws away the within-cell variation and
                # reports a different coefficient on a much smaller n.
                rows.append({"StockCode": c, "lead_time": lt, "fence": fence,
                             "shortfall": max(0, lt - fence),
                             "fill": m["fill"]})
        log(f"  lead time {lt}d")
    return pd.DataFrame(rows)


def fine(daily, profile, log=print):
    """Fine sweep at one lead time, across four window lengths.

    If the recovery were governed by the window length, the four curves would
    separate by the spread of those lengths. They do not.
    """
    items = D.sample(profile, daily).sample(
        min(C.FENCE_ITEMS, 4 * C.PER_QUADRANT), random_state=C.SAMPLE_SEED)
    base = {"replan_every": C.REPLAN_EVERY, "visibility": C.VISIBILITY_DAYS,
            "noise": C.BASE_SIGMA, "opening_stock_days": C.OPENING_STOCK_DAYS,
            "lead_time": C.FINE_LEAD}
    rows = []
    for L in C.FINE_PERIODS:
        cfg = {"name": f"Window {L}d", "kind": "float", "L": L}
        for fence in C.FINE_FENCES:
            res = [R.simulate(D.series(daily, c), cfg,
                              dict(base, coverage_fence=fence),
                              seed=R.stable_seed(c, L, fence))
                   for c in items["StockCode"]]
            rows.append({"L": L, "fence": fence,
                         "fill": float(np.mean([r["fill"] for r in res]))})
        log(f"  window {L}d")
    return pd.DataFrame(rows)


def cost_per_day(g):
    """Points of fill lost per day the fence falls short of the lead time.

    Ordinary least squares with heteroskedasticity-robust (HC1) errors.
    """
    d = g[g["shortfall"] >= 0]
    X = np.column_stack([np.ones(len(d)), d["shortfall"], d["lead_time"]])
    y = d["fill"].to_numpy(float)
    XtXi = np.linalg.pinv(X.T @ X)
    beta = XtXi @ X.T @ y
    resid = y - X @ beta
    S = (X * resid[:, None]).T @ (X * resid[:, None])
    cov = XtXi @ S @ XtXi * (len(d) / max(len(d) - X.shape[1], 1))
    se = np.sqrt(np.diag(cov))
    return {"points_per_day": -100 * beta[1], "t": beta[1] / se[1], "n": len(d)}


def recovery(f):
    """Smallest fence within half a point of the best fill, per window length."""
    out = {}
    for L, sub in f.groupby("L"):
        best = sub["fill"].max() * 100
        ok = sub[sub["fill"] * 100 >= best - 0.5]
        out[int(L)] = int(ok["fence"].min())
    return out
