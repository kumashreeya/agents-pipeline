"""
Experiment Runner: All 3 workflows on multiple HumanEval problems.
Saves structured JSON results for thesis analysis.
"""
import json
import time
import os
from human_eval.data import read_problems
from workflows.workflow_a import build_workflow_a
from workflows.workflow_b import build_workflow_b
from workflows.workflow_c import build_workflow_c


def make_initial_state(task_id, problem, max_iterations=3):
    return {
        "task_id": task_id,
        "prompt": problem["prompt"],
        "entry_point": problem["entry_point"],
        "code": "",
        "code_file": "",
        "syntax_valid": False,
        "quality_verdict": "",
        "quality_score": 0,
        "quality_feedback": "",
        "quality_plan": {},
        "quality_measurements": {},
        "test_pass_rate": 0,
        "test_coverage": 0,
        "test_total": 0,
        "test_passed": 0,
        "test_smells": 0,
        "test_flaky": False,
        "correct": False,
        "iteration": 0,
        "max_iterations": max_iterations,
        "total_tokens": 0,
    }


def run_workflow(name, builder, state):
    """Run one workflow and return results with timing."""
    start = time.time()
    try:
        wf = builder()
        result = wf.invoke(state)
        elapsed = round(time.time() - start, 1)
        return {
            "workflow": name,
            "task_id": result["task_id"],
            "iterations": result["iteration"],
            "correct": result["correct"],
            "quality_verdict": result["quality_verdict"],
            "quality_score": result["quality_score"],
            "test_pass_rate": result["test_pass_rate"],
            "test_passed": result["test_passed"],
            "test_total": result["test_total"],
            "test_coverage": result["test_coverage"],
            "test_smells": result["test_smells"],
            "test_flaky": result["test_flaky"],
            "time_seconds": elapsed,
            "error": None,
        }
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        print(f"  ERROR in {name}: {e}")
        return {
            "workflow": name,
            "task_id": state["task_id"],
            "iterations": state.get("iteration", 0),
            "correct": False,
            "quality_verdict": "ERROR",
            "quality_score": 0,
            "test_pass_rate": 0,
            "test_passed": 0,
            "test_total": 0,
            "test_coverage": 0,
            "test_smells": 0,
            "test_flaky": False,
            "time_seconds": elapsed,
            "error": str(e),
        }


def run_experiment(task_ids, max_iterations=3):
    """Run all 3 workflows on all given tasks."""
    problems = read_problems()
    
    workflows = [
        ("A_sequential", build_workflow_a),
        ("B_iterative", build_workflow_b),
        ("C_gated", build_workflow_c),
    ]
    
    all_results = []
    
    for task_id in task_ids:
        problem = problems[task_id]
        print(f"\n{'='*60}")
        print(f"TASK: {task_id}")
        print(f"{'='*60}")
        
        for wf_name, wf_builder in workflows:
            print(f"\n--- {wf_name} ---")
            state = make_initial_state(task_id, problem, max_iterations)
            result = run_workflow(wf_name, wf_builder, state)
            all_results.append(result)
            print(f"  Result: correct={result['correct']}, quality={result['quality_verdict']}({result['quality_score']}), tests={result['test_passed']}/{result['test_total']}, time={result['time_seconds']}s")
    
    return all_results


def print_summary(results):
    """Print comparison table."""
    # Group by task
    tasks = sorted(set(r["task_id"] for r in results))
    workflows = sorted(set(r["workflow"] for r in results))
    
    print(f"\n\n{'='*80}")
    print(f"EXPERIMENT SUMMARY")
    print(f"{'='*80}")
    
    # Per-task comparison
    for task in tasks:
        print(f"\n{task}:")
        print(f"  {'Workflow':<18} {'Correct':<10} {'Quality':<15} {'Tests':<12} {'Iters':<8} {'Time':<8}")
        print(f"  {'-'*70}")
        for wf in workflows:
            r = [x for x in results if x["task_id"] == task and x["workflow"] == wf]
            if r:
                r = r[0]
                q = f"{r['quality_verdict']}({r['quality_score']})"
                t = f"{r['test_passed']}/{r['test_total']}"
                print(f"  {wf:<18} {str(r['correct']):<10} {q:<15} {t:<12} {r['iterations']:<8} {r['time_seconds']:<8}")
    
    # Aggregate stats
    print(f"\n\nAGGREGATE:")
    print(f"  {'Workflow':<18} {'Correct%':<12} {'Avg Quality':<14} {'Avg Tests':<12} {'Avg Iters':<12} {'Avg Time':<10}")
    print(f"  {'-'*70}")
    for wf in workflows:
        wf_results = [r for r in results if r["workflow"] == wf]
        n = len(wf_results)
        if n > 0:
            correct_pct = round(sum(1 for r in wf_results if r["correct"]) / n * 100, 1)
            avg_quality = round(sum(r["quality_score"] for r in wf_results) / n, 1)
            avg_tests = round(sum(r["test_pass_rate"] for r in wf_results) / n, 2)
            avg_iters = round(sum(r["iterations"] for r in wf_results) / n, 1)
            avg_time = round(sum(r["time_seconds"] for r in wf_results) / n, 1)
            print(f"  {wf:<18} {correct_pct:<12} {avg_quality:<14} {avg_tests:<12} {avg_iters:<12} {avg_time:<10}")


if __name__ == "__main__":
    # Start with 5 problems
    task_ids = [f"HumanEval/{i}" for i in range(5)]
    
    print("Running experiment on 5 HumanEval problems x 3 workflows = 15 runs")
    print("This will take approximately 10-15 minutes...")
    
    results = run_experiment(task_ids, max_iterations=3)
    
    # Save results
    os.makedirs("experiment_results", exist_ok=True)
    with open("experiment_results/pilot_5_problems.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print_summary(results)
    
    print(f"\nResults saved to experiment_results/pilot_5_problems.json")
