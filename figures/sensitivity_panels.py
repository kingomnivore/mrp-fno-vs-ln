"""Which outcomes move with the forecast-error assumption, and which do not.

Plan stability is drawn in red because it is the only quantity that moves.
The other three are on scales wide enough to show movement and stay flat.
"""
import matplotlib.pyplot as plt

import style as S

NAME = "fig_sensitivity.png"


def render(s):
    panels = [("churn", "Plan stability (%)", 100, True),
              ("fill", "Fill rate (%)", 100, False),
              ("orders", "Orders per year", 1, False),
              ("elasticity_orders", "Order elasticity (%)", 1, False)]
    cols = {0.0: S.C_WARN, 0.5: S.C_LN, 0.8: S.C_FNO}
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.6))
    for ax, (key, lab, mult, fragile) in zip(axes, panels):
        for rho, g in s.groupby("persistence"):
            g = g.sort_values("sigma")
            ax.plot(100 * g["sigma"], mult * g[key], "-o", ms=4, lw=1.6,
                    color=cols.get(float(rho), S.C_BOTH),
                    label=f"persistence {rho}")
        ax.set_xlabel("Forecast error (%)")
        ax.set_title(lab, fontsize=10, color=S.C_WARN if fragile else S.INK)
        S.clean(ax)
        if not fragile:
            lo, hi = ax.get_ylim()
            mid = (hi + lo) / 2
            if hi - lo < 0.15 * abs(mid):
                ax.set_ylim(mid - 0.15 * abs(mid), mid + 0.15 * abs(mid))
    axes[0].legend(fontsize=8, loc="lower right")
    fig.suptitle("Outcomes against forecast error",
                 y=1.05, fontsize=12, fontweight="semibold")
    fig.tight_layout()
    fig.savefig(NAME, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return NAME
