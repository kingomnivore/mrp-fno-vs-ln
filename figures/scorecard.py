"""Balanced score by rule and business case, with ties marked as ties.

Three of the five cases are decided by under half a point on a hundred point
scale. Drawing those as victories would be a lie of presentation, so a margin
below the tie threshold boxes the top two with a dashed line instead.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import config as C
import style as S

NAME = "fig_scorecard.png"
LN_ONLY = ("Fixed order qty", "EOQ ratio")


def render(scored):
    order = list(dict.fromkeys(scored["config"]))
    piv = scored.pivot(index="config", columns="case",
                       values="Balanced").reindex(order)[list(C.CASES)]

    fig, ax = plt.subplots(figsize=(10.4, 5.4))
    im = ax.imshow(piv.to_numpy(), cmap="RdYlGn", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(C.CASES)),
                  [c.replace(" ", "\n", 1) for c in C.CASES], fontsize=9)
    ax.set_yticks(range(len(order)), order, fontsize=9)
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.to_numpy()[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=9,
                        color="#0b0b0b" if v > 35 else "white")
    for j, case in enumerate(C.CASES):
        col = piv[case].to_numpy()
        rank = np.argsort(-col)
        best, second = int(rank[0]), int(rank[1])
        if col[best] - col[second] >= C.TIE_MARGIN:
            ax.add_patch(plt.Rectangle((j - .5, best - .5), 1, 1, fill=False,
                                       edgecolor=S.INK, lw=2.4))
        else:
            for i in (best, second):
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                           edgecolor=S.INK, lw=1.6, ls=(0, (3, 2))))
    for i, cfg in enumerate(order):
        if cfg.startswith(LN_ONLY):
            ax.get_yticklabels()[i].set_color(S.C_LN)
            ax.get_yticklabels()[i].set_fontweight("semibold")
    ax.set_title("Balanced score by business case. A solid box is a clear winner,\n"
                 "a dashed pair is a tie. Orange labels are methods only LN documents.",
                 fontsize=11)
    fig.colorbar(im, ax=ax, label="Balanced score (100 is best in that case)",
                 shrink=0.85)
    fig.tight_layout()
    fig.savefig(NAME, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return NAME
