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
    """Laid out so nothing overlaps: the legend sits above the axes instead of
    over the bars, every bar carries its value, and the 0.5 point reference
    line is labelled in clear space at the left.
    """
    import textwrap
    from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

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

    fig, ax = plt.subplots(figsize=(11.0, 6.3))
    x = np.arange(len(d))
    w = 0.27
    cols = {"Service": S.C_WARN, "Working capital": S.C_FNO,
            "Planner workload": S.C_BOTH}
    for k, (cat, col) in enumerate(cols.items()):
        bars = ax.bar(x + (k - 1) * w, d[cat], w, color=col, label=cat)
        ax.bar_label(bars, fmt="%.0f", padding=4, fontsize=9, color=S.INK_2)

    # The old version carried a dashed line at 0.5 labelled "0.5 point of
    # fill". It referenced the spread among the time-phased rules only, which
    # is not what these bars plot, and it cost a whole empty decade of axis.
    # Section 4.1 states those figures in the text instead.
    ax.set_yscale("log")
    ax.set_ylim(7, 520)
    ax.yaxis.set_major_locator(FixedLocator([10, 20, 50, 100, 200]))
    ax.yaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))

    ax.set_xlim(-0.62, len(d) - 0.38)
    ax.set_xticks(x, [textwrap.fill(c, 13) for c in d.index], fontsize=10)
    ax.set_ylabel("Spread across the eleven settings (%)", fontsize=10)
    ax.set_title("Category spread by business case", fontsize=12, pad=40)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.005), ncol=3,
              frameon=False, fontsize=10, handlelength=1.4,
              columnspacing=2.4, borderaxespad=0)
    S.clean(ax)
    fig.tight_layout()
    fig.savefig(NAME, dpi=200, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)
    return NAME
