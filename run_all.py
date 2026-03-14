"""
Master experiment runner.
One command runs everything: experiments, charts, statistics, report.

Usage:
  python run_all.py --problems 5             # Quick pilot (5 problems)
  python run_all.py --problems 20            # Medium run
  python run_all.py --problems 164           # Full HumanEval
  python run_all.py --from 0 --to 49         # Custom range
  python run_all.py --problems 5 --verify    # With reproducibility check
"""
import argparse
import json
import os
import time
import datetime
from run_experiment import run_experiment, print_summary
from analyze_results import (
    load_results, bar_chart_correctness, bar_chart_quality,
    bar_chart_tests, cost_efficiency_chart, radar_chart,
    per_problem_heatmap, iteration_chart, summary_table
)
from analyze_statistics import analyze


def main():
    parser = argparse.ArgumentParser(description='Thesis Experiment Runner')
    parser.add_argument('--problems', type=int, default=5, help='Number of problems (from 0)')
    parser.add_argument('--from-p', type=int, default=0, help='Start problem index')
    parser.add_argument('--to-p', type=int, default=None, help='End problem index')
    parser.add_argument('--max-iter', type=int, default=3, help='Max iterations per workflow')
    parser.add_argument('--verify', action='store_true', help='Run reproducibility check')
    parser.add_argument('--output', type=str, default=None, help='Output filename')
    args = parser.parse_args()

    # Determine problem range
    from_p = args.from_p
    to_p = args.to_p if args.to_p is not None else from_p + args.problems - 1
    n_problems = to_p - from_p + 1
    n_runs = n_problems * 3
    est_time = n_runs * 20  # ~20 seconds per run estimate

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    output_name = args.output or f"experiment_{n_problems}p_{timestamp}"

    print("=" * 70)
    print("THESIS EXPERIMENT RUNNER")
    print("=" * 70)
    print(f"  Problems:       HumanEval/{from_p} to HumanEval/{to_p} ({n_problems} problems)")
    print(f"  Workflows:      A (sequential), B (iterative), C (quality-gated)")
    print(f"  Max iterations: {args.max_iter}")
    print(f"  Total runs:     {n_runs}")
    print(f"  Est. time:      {est_time // 60}m {est_time % 60}s")
    print(f"  Output:         experiment_results/{output_name}.json")
    print(f"  Verify:         {'Yes' if args.verify else 'No'}")
    print("=" * 70)

    # ==========================================
    # PHASE 1: Run experiments
    # ==========================================
    print(f"\n[PHASE 1/4] Running experiments...")
    start = time.time()

    task_ids = [f"HumanEval/{i}" for i in range(from_p, to_p + 1)]
    results = run_experiment(task_ids, max_iterations=args.max_iter)

    elapsed = round(time.time() - start, 1)
    print(f"\n[PHASE 1/4] Complete in {elapsed}s ({len(results)} results)")

    # Save results
    os.makedirs("experiment_results", exist_ok=True)
    results_file = f"experiment_results/{output_name}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Also save as latest
    with open("experiment_results/latest.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # ==========================================
    # PHASE 2: Summary table
    # ==========================================
    print(f"\n[PHASE 2/4] Generating summary...")
    print_summary(results)

    # ==========================================
    # PHASE 3: Charts
    # ==========================================
    print(f"\n[PHASE 3/4] Generating charts...")
    chart_dir = f"charts/{output_name}"
    os.makedirs(chart_dir, exist_ok=True)

    bar_chart_correctness(results, chart_dir)
    bar_chart_quality(results, chart_dir)
    bar_chart_tests(results, chart_dir)
    cost_efficiency_chart(results, chart_dir)
    radar_chart(results, chart_dir)
    per_problem_heatmap(results, chart_dir)
    iteration_chart(results, chart_dir)
    summary_table(results, chart_dir)

    print(f"  Charts saved to {chart_dir}/")

    # ==========================================
    # PHASE 4: Statistical analysis
    # ==========================================
    print(f"\n[PHASE 4/4] Statistical analysis...")
    analyze(results)

    # ==========================================
    # OPTIONAL: Reproducibility check
    # ==========================================
    if args.verify:
        print(f"\n[VERIFY] Reproducibility check on first 3 problems...")
        from workflows.workflow_a import build_workflow_a

        verify_ids = task_ids[:3]
        from human_eval.data import read_problems
        problems = read_problems()
        match = 0
        total = 0

        for tid in verify_ids:
            problem = problems[tid]
            state = {
                "task_id": tid, "prompt": problem["prompt"],
                "entry_point": problem["entry_point"],
                "code": "", "code_file": "", "syntax_valid": False,
                "quality_verdict": "", "quality_score": 0, "quality_feedback": "",
                "quality_plan": {}, "quality_measurements": {},
                "test_pass_rate": 0, "test_coverage": 0,
                "test_total": 0, "test_passed": 0, "test_smells": 0, "test_flaky": False,
                "correct": False,
                "iteration": 0, "max_iterations": args.max_iter, "total_tokens": 0,
                "ai_dead_code": 0, "ai_hallucinated_imports": 0, "ai_duplicates": 0,
            }

            wf = build_workflow_a()
            r1 = wf.invoke(dict(state))
            wf = build_workflow_a()
            r2 = wf.invoke(dict(state))

            total += 1
            if r1["code"] == r2["code"] and r1["correct"] == r2["correct"]:
                match += 1
                print(f"  {tid}: REPRODUCIBLE")
            else:
                print(f"  {tid}: DIFFERS")

        print(f"  Reproducibility: {match}/{total} ({round(match/total*100)}%)")

    # ==========================================
    # FINAL REPORT
    # ==========================================
    total_time = round(time.time() - start, 1)
    print(f"\n{'='*70}")
    print(f"EXPERIMENT COMPLETE")
    print(f"{'='*70}")
    print(f"  Total time:    {total_time // 60:.0f}m {total_time % 60:.0f}s")
    print(f"  Results:       {results_file}")
    print(f"  Charts:        {chart_dir}/")
    print(f"  Dashboard:     python server.py → http://127.0.0.1:5000")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
