"""Four window lengths, one lead time, swept across the coverage time fence.

If the window length governed where service recovers, these four curves would
separate by the spread of those lengths. They do not, which is why the article
withdrew an earlier claim that the fence must clear lead time plus a window.
"""
import numpy as np
import matplotlib.pyplot as plt

import config as C
import style as S

NAME = "fig_fence_rule.png"


def render(f):
    lt = C.FINE_LEAD
    fig, ax = plt.subplots(figsize=(8.8, 5.0))
    cols = ["#b0443a", "#b8761c", "#3a7d3a", "#2a78d6"]
    for (L, sub), c in zip(f.groupby("L"), cols):
        sub = sub.sort_values("fence")
        ax.plot(sub["fence"], 100 * sub["fill"], "-o", ms=4, lw=1.8, color=c,
                label=f"window {int(L)}d")
        ax.axvline(lt + L, color=c, lw=1.0, ls=":", alpha=0.55)
    ax.axvline(lt, color=S.INK, lw=2.0)
    ax.annotate(f"lead time, {lt} days", xy=(lt, ax.get_ylim()[0] + 1),
                xytext=(lt + 13, ax.get_ylim()[0] + 1.5), fontsize=9,
                color=S.INK, fontweight="semibold",
                arrowprops=dict(arrowstyle="->", color=S.INK, lw=1.1))
    ax.text(0.62, 0.30, "dotted lines mark lead time + window length,\n"
                        "where the cliff would sit if the window governed it",
            transform=ax.transAxes, fontsize=8.5, color=S.INK_2, ha="center")
    ax.set_xlabel("Coverage time fence (days)")
    ax.set_ylabel("Fill rate (%)")
    ax.set_title("Fill rate against coverage time fence", fontsize=12, pad=14)
    ax.legend(loc="lower right", fontsize=9)
    S.clean(ax)
    fig.tight_layout()
    fig.savefig(NAME, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return NAME
