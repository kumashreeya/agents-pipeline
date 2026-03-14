"""
Statistical analysis for thesis results.
Adds: confidence intervals, Mann-Whitney U test, effect sizes.
"""
import json
import os
import math


def load_results(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def mean(values):
    return sum(values) / len(values) if values else 0


def std_dev(values):
    if len(values) < 2:
        return 0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def confidence_interval_95(values):
    """95% confidence interval using t-distribution approximation."""
    n = len(values)
    if n < 2:
        return (0, 0)
    m = mean(values)
    se = std_dev(values) / math.sqrt(n)
    # t-value for 95% CI (approximation for small samples)
    t_vals = {2: 12.71, 3: 4.30, 4: 3.18, 5: 2.78, 6: 2.57, 7: 2.45,
              8: 2.37, 9: 2.31, 10: 2.26, 15: 2.14, 20: 2.09, 30: 2.04, 50: 2.01}
    t = 1.96  # default for large n
    for k in sorted(t_vals.keys()):
        if n <= k:
            t = t_vals[k]
            break
    return (round(m - t * se, 2), round(m + t * se, 2))


def mann_whitney_u(group1, group2):
    """
    Mann-Whitney U test (non-parametric).
    Tests if two groups come from the same distribution.
    Returns U statistic, z-score, and approximate p-value.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return {'U': 0, 'z': 0, 'p': 1.0, 'significant': False}

    # Rank all values together
    combined = [(v, 'g1') for v in group1] + [(v, 'g2') for v in group2]
    combined.sort(key=lambda x: x[0])

    # Assign ranks (handle ties by averaging)
    ranks = {}
    i = 0
    while i < len(combined):
        j = i
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        avg_rank = (i + j + 1) / 2  # 1-indexed average
        for k in range(i, j):
            if k not in ranks:
                ranks[k] = []
            ranks[k] = avg_rank
        i = j

    # Sum ranks for group 1
    r1 = sum(ranks[i] for i in range(len(combined)) if combined[i][1] == 'g1')

    U1 = r1 - n1 * (n1 + 1) / 2
    U2 = n1 * n2 - U1
    U = min(U1, U2)

    # Normal approximation for z-score
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (U - mu) / sigma if sigma > 0 else 0

    # Approximate p-value from z-score (two-tailed)
    # Using approximation: p ≈ 2 * exp(-0.7 * z^2)
    p = min(1.0, 2 * math.exp(-0.7 * z * z)) if abs(z) > 0 else 1.0

    return {
        'U': round(U, 2),
        'z': round(z, 3),
        'p_approx': round(p, 4),
        'significant_at_05': p < 0.05,
        'significant_at_01': p < 0.01,
        'n1': n1,
        'n2': n2,
    }


def cohens_d(group1, group2):
    """Effect size: Cohen's d."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0
    m1, m2 = mean(group1), mean(group2)
    s1, s2 = std_dev(group1), std_dev(group2)
    pooled_std = math.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0
    d = (m1 - m2) / pooled_std
    # Interpretation: 0.2=small, 0.5=medium, 0.8=large
    return round(d, 3)


def effect_size_label(d):
    d = abs(d)
    if d < 0.2: return "negligible"
    if d < 0.5: return "small"
    if d < 0.8: return "medium"
    return "large"


def analyze(results):
    """Full statistical analysis of experiment results."""
    workflows = sorted(set(r["workflow"] for r in results))

    print("=" * 80)
    print("STATISTICAL ANALYSIS")
    print("=" * 80)

    # Descriptive stats per workflow
    print("\n1. DESCRIPTIVE STATISTICS")
    print("-" * 80)
    print(f"{'Workflow':<18} {'N':<5} {'Correct%':<12} {'Quality':<20} {'Test Rate':<20} {'Time':<20}")
    print(f"{'':18} {'':5} {'':12} {'mean +/- std':<20} {'mean +/- std':<20} {'mean +/- std':<20}")
    print("-" * 80)

    wf_data = {}
    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        n = len(wr)
        correct_vals = [1 if r["correct"] else 0 for r in wr]
        quality_vals = [r["quality_score"] for r in wr]
        test_vals = [r["test_pass_rate"] for r in wr]
        time_vals = [r["time_seconds"] for r in wr]

        wf_data[wf] = {
            'correct': correct_vals,
            'quality': quality_vals,
            'test': test_vals,
            'time': time_vals,
        }

        cp = round(mean(correct_vals) * 100, 1)
        qm = round(mean(quality_vals), 1)
        qs = round(std_dev(quality_vals), 1)
        tm = round(mean(test_vals) * 100, 1)
        ts = round(std_dev(test_vals) * 100, 1)
        timem = round(mean(time_vals), 1)
        times = round(std_dev(time_vals), 1)

        print(f"{wf:<18} {n:<5} {cp:<12} {qm} +/- {qs:<12} {tm} +/- {ts:<12} {timem} +/- {times}")

    # Confidence intervals
    print("\n2. 95% CONFIDENCE INTERVALS")
    print("-" * 80)
    for metric_name, metric_key in [("Correctness", "correct"), ("Quality", "quality"), ("Test Rate", "test"), ("Time (s)", "time")]:
        print(f"\n  {metric_name}:")
        for wf in workflows:
            vals = wf_data[wf][metric_key]
            if metric_key == "correct":
                vals = [v * 100 for v in vals]
            elif metric_key == "test":
                vals = [v * 100 for v in vals]
            ci = confidence_interval_95(vals)
            print(f"    {wf:<18} [{ci[0]}, {ci[1]}]")

    # Pairwise comparisons
    print("\n3. PAIRWISE COMPARISONS (Mann-Whitney U)")
    print("-" * 80)
    pairs = [
        ("A_sequential", "B_iterative"),
        ("A_sequential", "C_gated"),
        ("B_iterative", "C_gated"),
    ]

    for metric_name, metric_key in [("Correctness", "correct"), ("Quality", "quality"), ("Test Rate", "test")]:
        print(f"\n  {metric_name}:")
        for wf1, wf2 in pairs:
            if wf1 in wf_data and wf2 in wf_data:
                g1 = wf_data[wf1][metric_key]
                g2 = wf_data[wf2][metric_key]
                mw = mann_whitney_u(g1, g2)
                d = cohens_d(g1, g2)
                sig = "*" if mw['significant_at_05'] else ""
                sig2 = "**" if mw['significant_at_01'] else ""
                marker = sig2 if sig2 else sig
                print(f"    {wf1} vs {wf2}: U={mw['U']}, z={mw['z']}, p={mw['p_approx']}{marker}, d={d} ({effect_size_label(d)})")

    print("\n  * p < 0.05, ** p < 0.01")

    # Summary findings
    print("\n4. KEY FINDINGS")
    print("-" * 80)

    for metric_name, metric_key in [("Correctness", "correct"), ("Quality", "quality")]:
        best_wf = max(workflows, key=lambda w: mean(wf_data[w][metric_key]))
        worst_wf = min(workflows, key=lambda w: mean(wf_data[w][metric_key]))
        best_val = round(mean(wf_data[best_wf][metric_key]) * (100 if metric_key in ['correct', 'test'] else 1), 1)
        worst_val = round(mean(wf_data[worst_wf][metric_key]) * (100 if metric_key in ['correct', 'test'] else 1), 1)
        d = cohens_d(wf_data[best_wf][metric_key], wf_data[worst_wf][metric_key])
        mw = mann_whitney_u(wf_data[best_wf][metric_key], wf_data[worst_wf][metric_key])
        print(f"  {metric_name}: {best_wf} ({best_val}) vs {worst_wf} ({worst_val}), effect={effect_size_label(d)}, p={mw['p_approx']}")

    fastest = min(workflows, key=lambda w: mean(wf_data[w]['time']))
    slowest = max(workflows, key=lambda w: mean(wf_data[w]['time']))
    print(f"  Time: {fastest} ({round(mean(wf_data[fastest]['time']),1)}s) vs {slowest} ({round(mean(wf_data[slowest]['time']),1)}s)")


if __name__ == "__main__":
    results_dir = "experiment_results"
    files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json')]) if os.path.exists(results_dir) else []

    if not files:
        print("No results found. Run experiments first.")
        exit(1)

    latest = os.path.join(results_dir, files[-1])
    print(f"Loading: {latest}")
    results = load_results(latest)
    print(f"Data points: {len(results)}")
    analyze(results)
