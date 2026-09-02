"""Which results depend on the forecast-error assumption, and which do not.

Forecast error is not in the data and not in either vendor's documentation.
It is a parameter, so every plan-stability figure rests on it. Both its size
and its persistence between runs are swept here, and the article reports only
what holds across the whole range.

One result moves in a direction the literature predicts: days of cover rise
with forecast error. Wemmerlov (1989) reports that forecast errors "not only
lead to stockouts, they also induce larger inventories".
"""
import numpy as np
import pandas as pd

import config as C
import data as D
import rolling as R


def _elasticity(d, target):
    """Per cent change in `target` for a doubling of the window length.

    Both elasticities run on the same rows, and log2 needs strictly positive
    inputs. Filtering on orders alone leaves a zero cover_days in the design
    matrix, which returns nan for the whole column.
    """
    p = d[(d["orders_per_year"] > 0) & (d["cover_days"] > 0)]
    X = np.column_stack([np.ones(len(p)), np.log2(p["L"])])
    beta = np.linalg.lstsq(X, np.log2(p[target]), rcond=None)[0]
    return 100 * (2 ** beta[1] - 1)


def run(daily, profile, log=print):
    items = D.sample(profile, daily)
    cfgs = [{"name": f"Window {L}d", "kind": "float", "L": L}
            for L in C.PERIODS]
    base = {"lead_time": 5, "replan_every": C.REPLAN_EVERY,
            "visibility": C.VISIBILITY_DAYS,
            "opening_stock_days": C.OPENING_STOCK_DAYS}
    out = []
    for rho in C.PERSISTENCE:
        for sigma in C.SIGMAS:
            rows = []
            sc = dict(base, noise=sigma, noise_persistence=rho)
            for _, it in items.iterrows():
                a = D.series(daily, it["StockCode"])
                for cfg in cfgs:
                    rows.append({"L": cfg["L"],
                                 **R.simulate(a, cfg, sc,
                                              seed=R.stable_seed(it["StockCode"],
                                                                 cfg["name"]))})
            d = pd.DataFrame(rows)
            out.append({
                "persistence": rho, "sigma": sigma,
                "churn": d["order_churn"].mean(),
                "fill": d["fill"].mean(),
                "cover": d["cover_days"].mean(),
                "orders": d["orders_per_year"].mean(),
                "elasticity_orders": _elasticity(d, "orders_per_year"),
                "elasticity_cover": _elasticity(d, "cover_days"),
            })
        log(f"  persistence {rho}")
    return pd.DataFrame(out)


def verdicts(s):
    """Range of each outcome across the whole assumption grid."""
    rows = []
    for key, label, fmt in [
            ("churn", "Plan stability", "pct"),
            ("fill", "Fill rate", "pct"),
            ("orders", "Orders per item per year", "raw"),
            ("cover", "Days of cover", "raw"),
            ("elasticity_orders", "Order elasticity to window length", "raw"),
            ("elasticity_cover", "Cover elasticity to window length", "raw")]:
        lo, hi = float(s[key].min()), float(s[key].max())
        if fmt == "pct":
            lo, hi = 100 * lo, 100 * hi
        span = abs(hi - lo) / max(abs((hi + lo) / 2), 1e-9)
        rows.append({"result": label, "low": lo, "high": hi,
                     "verdict": "depends on the assumption" if span > 0.25
                                else "robust"})
    return pd.DataFrame(rows)
