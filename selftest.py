"""Four structural checks. Identities, not plausibility tests.

Three of these failed the first time they were written, and each failure was a
real defect that would otherwise have reached the article:

  - the Wagner and Whitin dynamic programme tiled calendar periods where it
    should have tiled demand occurrences, and returned values above the true
    optimum, which silently weakened the bound it exists to provide;
  - the replay committed orders on their receipt date rather than their release
    date, so nothing was ever ordered in time and fill collapsed to 1.9%;
  - runs were seeded from Python's hash(), which is salted per process, so the
    published figures would not have reproduced on anyone else's machine.

Run this before reading any result.
"""
import numpy as np

import config as C
import engine as E
import rolling as R


def _demand(rng, n=120, p=0.45, hi=60):
    return (rng.random(n) < p) * rng.integers(1, hi, n).astype(float)


def check_wagner_whitin(trials=200, seed=1):
    """No lot-sizing rule may cost less than the exact optimum."""
    rng = np.random.default_rng(seed)
    worst = 0.0
    for _ in range(trials):
        d = _demand(rng)
        if d.sum() <= 0:
            continue
        for setup, hold in ((50.0, 1.0), (500.0, 1.0), (50.0, 0.1)):
            opt = E.wagner_whitin(d, setup, hold)
            for orders in (E.lot_for_lot(d),
                           E.period_floating(d, 7),
                           E.period_anchored(d, 7, 0),
                           E.period_anchored_at_need(d, 7, 0),
                           E.period_varying(d, 7, 28, 56)):
                cost = E.cost_of(orders, d, setup, hold)
                worst = min(worst, cost - opt)
    return worst >= -1e-6, f"smallest margin above the optimum: {worst:+.6f}"


def check_unit_bucket(trials=200, seed=2):
    """A one day bucket must reproduce one order per requirement exactly."""
    rng = np.random.default_rng(seed)
    bad = 0
    for _ in range(trials):
        d = _demand(rng)
        for fn in (E.period_floating,
                   lambda x, L: E.period_anchored(x, L, 0),
                   lambda x, L: E.period_anchored_at_need(x, L, 0)):
            if not np.array_equal(fn(d, 1), E.lot_for_lot(d)):
                bad += 1
    return bad == 0, f"{bad} mismatches across {trials} series and three rules"


def check_zero_noise(daily, profile, items=20):
    """With a perfect forecast, a calendar-anchored plan must never move.

    A floating bucket may still move, because its boundaries are defined by the
    demand rather than by the calendar. That is the mechanism, not a defect,
    which is why only the anchored rules are asserted here.
    """
    import data as D
    sample = D.sample(profile, daily, per_quadrant=max(1, items // 4))
    scenario = {"lead_time": 0, "replan_every": C.REPLAN_EVERY,
                "visibility": C.VISIBILITY_DAYS, "noise": 0.0,
                "opening_stock_days": C.OPENING_STOCK_DAYS}
    worst = 0.0
    for _, it in sample.iterrows():
        a = D.series(daily, it["StockCode"])
        for cfg in ({"name": "anch14", "kind": "anch_need", "L": 14},
                    {"name": "l4l", "kind": "l4l", "L": 1}):
            m = R.simulate(a, cfg, scenario, seed=R.stable_seed(it["StockCode"], cfg["name"]))
            worst = max(worst, m["PCR"])
    return worst < 1e-12, f"largest plan churn on a perfect forecast: {worst:.2e}"


def check_reproducible():
    """The seed must not depend on the interpreter session."""
    a = R.stable_seed("85123A", "Period 14d", "Long-lead importer")
    b = R.stable_seed("85123A", "Period 14d", "Long-lead importer")
    known = 2560379992   # CRC32 of the joined key; fixed across sessions
    return (a == b == known), f"stable_seed returned {a}, expected {known}"


def run_all(daily, profile, log=print):
    log("Structural checks")
    results = [
        ("no rule beats the Wagner and Whitin optimum", *check_wagner_whitin()),
        ("a one day bucket equals one order per requirement", *check_unit_bucket()),
        ("a calendar-anchored plan does not move on a perfect forecast",
         *check_zero_noise(daily, profile)),
        ("results reproduce in a fresh process", *check_reproducible()),
    ]
    ok = True
    for name, passed, detail in results:
        ok &= passed
        log(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        log(f"         {detail}")
    if not ok:
        raise SystemExit("A structural check failed. Nothing downstream is safe.")
    return results
