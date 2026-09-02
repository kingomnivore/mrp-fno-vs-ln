"""How much each category actually separates the rules, per business case.

Working capital and planner workload move by tens of per cent. Service moves
far less, and most of what it does move comes from the one reorder-point rule.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config as C
import style as S

NAME = "fig_category_spread.png"


def render(scored):
    rows = []
    for case in C.CASES:
        s = scored[scored["case"] == case]
        rows.append({
            "case": case,
            "Service": 100 * float(s["fill"].max() - s["fill"].min()),
            "Working capital": 100 * float(s["cover_days"].max() - s["cover_days"].min())
            / float(s["cover_days"].mean()),
            "Planner workload": 100 * float(s["orders_per_year"].max() - s["orders_per_year"].min())
            / float(s["orders_per_year"].mean())})
    d = pd.DataFrame(rows).set_index("case")

    fig, ax = plt.subplots(figsize=(9.4, 4.6))
    x = np.arange(len(d))
    w = 0.26
    cols = {"Service": S.C_WARN, "Working capital": S.C_FNO,
            "Planner workload": S.C_BOTH}
    for k, (cat, col) in enumerate(cols.items()):
        ax.bar(x + (k - 1) * w, d[cat], w, color=col, label=cat)
    ax.set_yscale("log")
    ax.set_xticks(x, [c.replace(" ", "\n", 1) for c in d.index], fontsize=9)
    ax.set_ylabel("Spread across the eleven rules (%)")
    ax.set_title("Stock and order count move by tens of per cent.\n"
                 "Service moves far less.", fontsize=11)
    ax.legend(fontsize=9)
    S.clean(ax)
    fig.tight_layout()
    fig.savefig(NAME, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return NAME
