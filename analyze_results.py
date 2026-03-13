"""
Analysis scripts: Generate charts and tables for thesis.
Uses experiment results JSON files.
"""
import json
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def load_results(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def bar_chart_correctness(results, output_dir):
    """Bar chart: Correctness % per workflow."""
    workflows = sorted(set(r["workflow"] for r in results))
    correct_pct = []
    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        pct = sum(1 for r in wr if r["correct"]) / len(wr) * 100
        correct_pct.append(round(pct, 1))

    colors = ['#4A90D9', '#E8913A', '#50B86C']
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(workflows, correct_pct, color=colors, width=0.5, edgecolor='black', linewidth=0.5)

    for bar, val in zip(bars, correct_pct):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5, f'{val}%', ha='center', fontsize=12, fontweight='bold')

    ax.set_ylabel('Correctness (%)', fontsize=12)
    ax.set_title('Functional Correctness by Workflow Variant', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'correctness_by_workflow.png'), dpi=150)
    plt.close()
    print("  Saved: correctness_by_workflow.png")


def bar_chart_quality(results, output_dir):
    """Bar chart: Average quality score per workflow."""
    workflows = sorted(set(r["workflow"] for r in results))
    avg_quality = []
    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        avg = sum(r["quality_score"] for r in wr) / len(wr)
        avg_quality.append(round(avg, 1))

    colors = ['#4A90D9', '#E8913A', '#50B86C']
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(workflows, avg_quality, color=colors, width=0.5, edgecolor='black', linewidth=0.5)

    for bar, val in zip(bars, avg_quality):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5, f'{val}', ha='center', fontsize=12, fontweight='bold')

    ax.set_ylabel('Average Quality Score', fontsize=12)
    ax.set_title('Quality Score by Workflow Variant', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'quality_by_workflow.png'), dpi=150)
    plt.close()
    print("  Saved: quality_by_workflow.png")


def bar_chart_tests(results, output_dir):
    """Bar chart: Average test pass rate per workflow."""
    workflows = sorted(set(r["workflow"] for r in results))
    avg_tests = []
    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        avg = sum(r["test_pass_rate"] for r in wr) / len(wr)
        avg_tests.append(round(avg * 100, 1))

    colors = ['#4A90D9', '#E8913A', '#50B86C']
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(workflows, avg_tests, color=colors, width=0.5, edgecolor='black', linewidth=0.5)

    for bar, val in zip(bars, avg_tests):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5, f'{val}%', ha='center', fontsize=12, fontweight='bold')

    ax.set_ylabel('Test Pass Rate (%)', fontsize=12)
    ax.set_title('AI-Generated Test Pass Rate by Workflow', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'test_rate_by_workflow.png'), dpi=150)
    plt.close()
    print("  Saved: test_rate_by_workflow.png")


def cost_efficiency_chart(results, output_dir):
    """Scatter plot: Correctness vs Time (cost-quality tradeoff)."""
    workflows = sorted(set(r["workflow"] for r in results))
    colors_map = {'A_sequential': '#4A90D9', 'B_iterative': '#E8913A', 'C_gated': '#50B86C'}

    fig, ax = plt.subplots(figsize=(8, 6))

    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        avg_time = sum(r["time_seconds"] for r in wr) / len(wr)
        correct_pct = sum(1 for r in wr if r["correct"]) / len(wr) * 100
        avg_iters = sum(r["iterations"] for r in wr) / len(wr)

        ax.scatter(avg_time, correct_pct, s=200, color=colors_map.get(wf, 'gray'),
                   edgecolor='black', linewidth=1, zorder=5, label=f'{wf} ({avg_iters:.1f} iters)')

    ax.set_xlabel('Average Time (seconds)', fontsize=12)
    ax.set_ylabel('Correctness (%)', fontsize=12)
    ax.set_title('Cost-Quality Tradeoff: Time vs Correctness', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'cost_quality_tradeoff.png'), dpi=150)
    plt.close()
    print("  Saved: cost_quality_tradeoff.png")


def radar_chart(results, output_dir):
    """Radar chart: Multi-dimensional comparison of workflows."""
    workflows = sorted(set(r["workflow"] for r in results))
    
    # Dimensions to compare
    dimensions = ['Correctness', 'Quality', 'Test Rate', 'Coverage', 'Efficiency']
    
    data = {}
    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        n = len(wr)
        correct = sum(1 for r in wr if r["correct"]) / n * 100
        quality = sum(r["quality_score"] for r in wr) / n
        test_rate = sum(r["test_pass_rate"] for r in wr) / n * 100
        coverage = sum(r["test_coverage"] for r in wr) / n
        # Efficiency: inverse of iterations (fewer = better), scaled to 100
        avg_iters = sum(r["iterations"] for r in wr) / n
        max_iters = max(r.get("max_iterations", 3) for r in wr)
        efficiency = (1 - (avg_iters - 1) / max(max_iters - 1, 1)) * 100
        
        data[wf] = [correct, quality, test_rate, coverage, efficiency]

    # Create radar
    angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
    angles += angles[:1]

    colors_map = {'A_sequential': '#4A90D9', 'B_iterative': '#E8913A', 'C_gated': '#50B86C'}

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for wf in workflows:
        values = data[wf] + data[wf][:1]
        ax.plot(angles, values, 'o-', linewidth=2, label=wf, color=colors_map.get(wf, 'gray'))
        ax.fill(angles, values, alpha=0.1, color=colors_map.get(wf, 'gray'))

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions, fontsize=11)
    ax.set_ylim(0, 100)
    ax.set_title('Multi-Dimensional Workflow Comparison', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'radar_comparison.png'), dpi=150)
    plt.close()
    print("  Saved: radar_comparison.png")


def per_problem_heatmap(results, output_dir):
    """Heatmap: Correctness per problem per workflow."""
    tasks = sorted(set(r["task_id"] for r in results))
    workflows = sorted(set(r["workflow"] for r in results))

    matrix = []
    for task in tasks:
        row = []
        for wf in workflows:
            r = [x for x in results if x["task_id"] == task and x["workflow"] == wf]
            if r:
                row.append(1 if r[0]["correct"] else 0)
            else:
                row.append(0)
        matrix.append(row)

    matrix = np.array(matrix)
    task_labels = [t.replace("HumanEval/", "HE/") for t in tasks]

    fig, ax = plt.subplots(figsize=(6, max(4, len(tasks) * 0.4 + 1)))
    cmap = plt.cm.colors.ListedColormap(['#FF6B6B', '#50B86C'])
    im = ax.imshow(matrix, cmap=cmap, aspect='auto')

    ax.set_xticks(range(len(workflows)))
    ax.set_xticklabels(workflows, fontsize=10, rotation=15)
    ax.set_yticks(range(len(tasks)))
    ax.set_yticklabels(task_labels, fontsize=9)

    for i in range(len(tasks)):
        for j in range(len(workflows)):
            text = "PASS" if matrix[i, j] == 1 else "FAIL"
            color = "white"
            ax.text(j, i, text, ha="center", va="center", fontsize=8, fontweight="bold", color=color)

    ax.set_title('Correctness per Problem per Workflow', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'correctness_heatmap.png'), dpi=150)
    plt.close()
    print("  Saved: correctness_heatmap.png")


def iteration_chart(results, output_dir):
    """Bar chart: Average iterations per workflow."""
    workflows = sorted(set(r["workflow"] for r in results))
    avg_iters = []
    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        avg = sum(r["iterations"] for r in wr) / len(wr)
        avg_iters.append(round(avg, 1))

    colors = ['#4A90D9', '#E8913A', '#50B86C']
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(workflows, avg_iters, color=colors, width=0.5, edgecolor='black', linewidth=0.5)

    for bar, val in zip(bars, avg_iters):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, f'{val}', ha='center', fontsize=12, fontweight='bold')

    ax.set_ylabel('Average Iterations', fontsize=12)
    ax.set_title('Compute Cost: Iterations per Workflow', fontsize=14, fontweight='bold')
    ax.set_ylim(0, max(avg_iters) + 1)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'iterations_by_workflow.png'), dpi=150)
    plt.close()
    print("  Saved: iterations_by_workflow.png")


def summary_table(results, output_dir):
    """Generate a summary table as text file."""
    workflows = sorted(set(r["workflow"] for r in results))

    lines = []
    lines.append("WORKFLOW COMPARISON SUMMARY")
    lines.append("=" * 80)
    lines.append(f"{'Metric':<22} {'A_sequential':<16} {'B_iterative':<16} {'C_gated':<16}")
    lines.append("-" * 70)

    metrics_to_show = [
        ("Correct %", lambda wr: f"{sum(1 for r in wr if r['correct'])/len(wr)*100:.1f}%"),
        ("Avg Quality Score", lambda wr: f"{sum(r['quality_score'] for r in wr)/len(wr):.1f}"),
        ("Avg Test Pass Rate", lambda wr: f"{sum(r['test_pass_rate'] for r in wr)/len(wr)*100:.1f}%"),
        ("Avg Coverage", lambda wr: f"{sum(r['test_coverage'] for r in wr)/len(wr):.1f}%"),
        ("Avg Iterations", lambda wr: f"{sum(r['iterations'] for r in wr)/len(wr):.1f}"),
        ("Avg Time (s)", lambda wr: f"{sum(r['time_seconds'] for r in wr)/len(wr):.1f}"),
        ("Avg Dead Code", lambda wr: f"{sum(r.get('ai_dead_code',0) for r in wr)/len(wr):.1f}"),
        ("Avg Duplicates", lambda wr: f"{sum(r.get('ai_duplicates',0) for r in wr)/len(wr):.1f}"),
        ("Avg Test Smells", lambda wr: f"{sum(r.get('test_smells',0) for r in wr)/len(wr):.1f}"),
    ]

    for metric_name, calc_fn in metrics_to_show:
        row = f"{metric_name:<22}"
        for wf in workflows:
            wr = [r for r in results if r["workflow"] == wf]
            row += f" {calc_fn(wr):<16}"
        lines.append(row)

    table_text = "\n".join(lines)
    print(table_text)

    with open(os.path.join(output_dir, 'summary_table.txt'), 'w') as f:
        f.write(table_text)
    print(f"\n  Saved: summary_table.txt")


if __name__ == "__main__":
    # Find the most recent results file
    results_dir = "experiment_results"
    files = sorted([f for f in os.listdir(results_dir) if f.endswith('.json')]) if os.path.exists(results_dir) else []

    if not files:
        print("No experiment results found. Run run_experiment.py first.")
        exit(1)

    latest = os.path.join(results_dir, files[-1])
    print(f"Loading results from: {latest}")
    results = load_results(latest)
    print(f"Loaded {len(results)} data points")

    output_dir = "charts"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nGenerating charts...")
    bar_chart_correctness(results, output_dir)
    bar_chart_quality(results, output_dir)
    bar_chart_tests(results, output_dir)
    cost_efficiency_chart(results, output_dir)
    radar_chart(results, output_dir)
    per_problem_heatmap(results, output_dir)
    iteration_chart(results, output_dir)

    print(f"\nGenerating summary table...")
    summary_table(results, output_dir)

    print(f"\nAll charts saved to {output_dir}/")
    print(f"Files:")
    for f in sorted(os.listdir(output_dir)):
        print(f"  {f}")
