"""The same items, classified in two different review periods.

SBC define the demand interval in review periods, not days, so the period is
part of the measure. An item is not lumpy on its own account.
"""
import numpy as np
import matplotlib.pyplot as plt

import config as C
import style as S

NAME = "fig_classification.png"


def render(by_period):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharex=True, sharey=True)
    for ax, period in zip(axes, ("daily", "monthly")):
        df = by_period[period]
        x = np.clip(df["ADI"], 0.5, 200)
        y = np.clip(df["CV2"], 0.01, 60)
        ax.scatter(x, y, s=7, c=[S.QUAD[q] for q in df["quadrant"]],
                   alpha=0.45, linewidths=0)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.axvline(C.ADI_CUT, color=S.INK_2, lw=0.9, ls="--")
        ax.axhline(C.CV2_CUT, color=S.INK_2, lw=0.9, ls="--")
        share = df["quadrant"].value_counts(normalize=True)
        ax.set_title(f"Measured in {period} buckets\n"
                     f"lumpy {100 * share.get('lumpy', 0):.0f}%   "
                     f"smooth {100 * share.get('smooth', 0):.0f}%")
        ax.set_xlabel("Average demand interval (buckets)")
        S.clean(ax, value_axis=None)
    axes[0].set_ylabel("Squared coefficient of variation")
    fig.suptitle("The demand class is a property of the review period, "
                 "not of the item alone", y=1.0, fontsize=12, fontweight="semibold")
    fig.tight_layout()
    fig.savefig(NAME, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return NAME
