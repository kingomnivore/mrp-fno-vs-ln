"""Entry point. Reproduces every number in the article.

    python run.py

Writes outputs.txt and six figures into the working directory. The source
workbook downloads on first run and is cached, so the first run is slower.
"""
import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd

import config as C
import data as D
import external
import fence
import report
import scenarios
import selftest
import sensitivity
import style
from figures import (classification, fence_rule, scorecard, spread,
                     sensitivity_panels, tradeoff)


def main():
    out = report.Report()

    print("Loading demand...")
    daily = D.daily_demand()
    codes = D.active_items(daily)
    by_period = {p: D.classify(daily, codes, p) for p in C.REVIEW_PERIODS}
    profile = by_period[C.HEADLINE_PERIOD]

    # ---------------------------------------------------------------- checks
    # These run first and abort on failure. Nothing downstream is safe if an
    # identity does not hold.
    print("\nStructural checks...")
    structural = selftest.run_all(daily, profile, log=lambda s: None)
    ext = external.run()

    report.source(out, D.source_summary(), codes, profile)
    report.classification(out, by_period)
    report.checks(out, ext, structural)

    # --------------------------------------------------------- business cases
    print("\nBusiness cases...")
    raw, scored, spreads = scenarios.run(daily, profile)
    win = scenarios.winners(scored)
    tp = scenarios.time_phased_service(scored)
    report.cases(out, scored, win, tp)
    scored.to_csv("results_cases.csv", index=False)

    # --------------------------------------------------------- the trade-off
    print("\nWindow length trade-off...")
    tr = tradeoff.data(daily, profile)
    tr.to_csv("results_tradeoff.csv", index=False)
    report.tradeoff(out, tradeoff.elasticities(tr))

    # ---------------------------------------------------------------- fences
    print("\nCoverage time fence...")
    g = fence.grid(daily, profile, log=lambda s: None)
    f = fence.fine(daily, profile, log=lambda s: None)
    g.to_csv("results_fence_grid.csv", index=False)
    f.to_csv("results_fence_fine.csv", index=False)
    report.fences(out, g, f, fence.cost_per_day(g), fence.recovery(f))

    # ----------------------------------------------------------- sensitivity
    print("\nForecast error sweep...")
    s = sensitivity.run(daily, profile, log=lambda x: None)
    s.to_csv("results_sensitivity.csv", index=False)
    report.sensitivity_section(out, s, sensitivity.verdicts(s))

    out.save(C.OUTPUTS)

    # --------------------------------------------------------------- figures
    print("\nFigures...")
    style.apply()
    written = [
        spread.render(scored),
        scorecard.render(scored),
        tradeoff.render(tr),
        classification.render(by_period),
        fence_rule.render(f),
        sensitivity_panels.render(s),
    ]
    print("\nwrote %s and %s" % (C.OUTPUTS, ", ".join(written)))


if __name__ == "__main__":
    main()
