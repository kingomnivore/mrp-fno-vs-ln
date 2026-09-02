"""Builds outputs.txt. One function per section, and every number the article
quotes appears here."""
import io


class Report:
    def __init__(self):
        self.lines = []

    def __call__(self, text=""):
        self.lines.append(str(text))
        print(text)

    def rule(self, title):
        self("")
        self("=" * 74)
        self(title)
        self("=" * 74)

    def save(self, path):
        io.open(path, "w", encoding="utf-8").write("\n".join(self.lines) + "\n")


def source(out, summary, items, profile):
    out.rule("1. SOURCE")
    out(f"  rows                     {summary['rows']:,}")
    out(f"  distinct stock codes     {summary['codes']:,}")
    out(f"  date range               {summary['date_min']} to {summary['date_max']}")
    out(f"  non-item codes excluded  {summary['non_item_codes']}")
    out(f"  negative-quantity rows   {summary['negative_rows']:,}")
    out(f"  on credit invoices       {summary['credit_rows']:,}")
    out(f"  negatives outside them   {summary['negative_outside_credits']:,}")
    out(f"  largest single credit    {summary['largest_credit']:,}")
    out(f"  items passing filter     {len(items):,}")
    out("")
    out("  Classification, weekly review period:")
    for q in ("smooth", "intermittent", "erratic", "lumpy"):
        out(f"    {q:<14} {int((profile['quadrant'] == q).sum()):>6,}")


def classification(out, by_period):
    out.rule("2. THE CLASSIFICATION MOVES WITH THE REVIEW PERIOD")
    out("  Same items throughout. Only the measurement period changes.")
    out("")
    out(f"  {'period':<12}" + "".join(f"{q:>15}" for q in
        ("smooth", "intermittent", "erratic", "lumpy")))
    for period, prof in by_period.items():
        share = prof["quadrant"].value_counts(normalize=True)
        out(f"  {period:<12}" + "".join(
            f"{100 * share.get(q, 0.0):>14.1f}%" for q in
            ("smooth", "intermittent", "erratic", "lumpy")))


def checks(out, ext, structural):
    out.rule("3. CHECKS THAT RAN BEFORE ANY RESULT")
    out("  External: this firm's order book against its own sector")
    out(f"    overlapping complete months   {ext['months']}  "
        f"({ext['from']} to {ext['to']})")
    out(f"    correlation, levels           {ext['r_levels']:.3f}")
    out(f"    correlation, logs             {ext['r_logs']:.3f}")
    out(f"    peak month                    firm {ext['peak_dataset']}, "
        f"sector {ext['peak_ons']}")
    out(f"    November against own mean     firm {ext['nov_ratio_dataset']:.2f}x, "
        f"sector {ext['nov_ratio_ons']:.2f}x")
    out("")
    out("  Structural identities:")
    for name, passed, detail in structural:
        out(f"    [{'PASS' if passed else 'FAIL'}] {name}")
        out(f"           {detail}")


def cases(out, scored, win, tp_service):
    out.rule("4. FIVE BUSINESS CASES, ELEVEN LOT-SIZING RULES")
    for case in win["case"]:
        sub = scored[scored["case"] == case].sort_values(
            "Balanced", ascending=False)
        out("")
        out(f"  {case}")
        out(f"    {'rule':<30}{'who':<10}{'fill':>7}{'cover':>8}"
            f"{'orders':>8}{'balanced':>10}")
        for _, r in sub.iterrows():
            out(f"    {r['config']:<30}{r['who']:<10}{r['fill']:>7.3f}"
                f"{r['cover_days']:>8.1f}{r['orders_per_year']:>8.1f}"
                f"{r['Balanced']:>10.2f}")
    out("")
    out("  Winners and margins:")
    for _, r in win.iterrows():
        out(f"    {r['case']:<28}{r['Balanced']:<30}"
            f"margin {r['margin']:>6.2f}  {r['verdict']}")
    out("")
    out("  Service spread among time-phased rules only (points of fill):")
    for case, sp in tp_service.items():
        out(f"    {case:<28}{sp:>6.2f}")


def fences(out, g, f, cost, rec):
    out.rule("6. THE COVERAGE TIME FENCE")
    out("  Fill rate (%), rows = lead time, cols = fence, one window length")
    piv = g.pivot_table(index="lead_time", columns="fence",
                        values="fill", aggfunc="mean") * 100
    out("    " + piv.round(1).to_string().replace("\n", "\n    "))
    out("")
    out(f"  Each day the fence falls short of the lead time costs "
        f"{cost['points_per_day']:.3f} points of fill")
    out(f"    robust t = {cost['t']:.1f}, n = {cost['n']:,}")
    out("")
    out(f"  Fine sweep at a {f['fence'].min()}+ day fence, "
        f"four window lengths, one lead time:")
    piv2 = f.pivot(index="L", columns="fence", values="fill") * 100
    out("    " + piv2.round(1).to_string().replace("\n", "\n    "))
    out("")
    out("  Smallest fence within half a point of the best fill:")
    for L, fence in rec.items():
        out(f"    window {L:>3}d -> fence {fence}d")
    out("  If the window length governed the recovery these would fan out.")


def sensitivity_section(out, s, v):
    out.rule("7. WHAT THE RESULTS REST ON")
    out("  Forecast error is a parameter, not a property of the data.")
    out("")
    out("  Mean plan stability (%), rows = persistence, cols = error size")
    piv = s.pivot(index="persistence", columns="sigma", values="churn") * 100
    out("    " + piv.round(1).to_string().replace("\n", "\n    "))
    out("")
    for _, r in v.iterrows():
        out(f"    {r['result']:<38}{r['low']:>9.2f} to {r['high']:>9.2f}"
            f"   {r['verdict']}")


def tradeoff(out, elasticities):
    out.rule("5. WHAT THE WINDOW LENGTH BUYS AND COSTS")
    n = elasticities.get("_n")
    for label, e in elasticities.items():
        if label.startswith("_"):
            continue
        out(f"  doubling the window changes {label:<22}{e:>+7.1f}%")
    if n:
        out(f"  n = {n:,} item-configurations, common to both regressions")
