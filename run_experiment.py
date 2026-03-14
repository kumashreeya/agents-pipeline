"""Experiment Runner: 3 workflows on multiple HumanEval problems."""
import json
import time
import os
from human_eval.data import read_problems
from workflows.workflow_a import build_workflow_a
from workflows.workflow_b import build_workflow_b
from workflows.workflow_c import build_workflow_c


def make_initial_state(task_id, problem, max_iterations=3):
    return {
        "task_id": task_id, "prompt": problem["prompt"],
        "entry_point": problem["entry_point"],
        "code": "", "code_file": "", "syntax_valid": False,
        "quality_verdict": "", "quality_score": 0, "quality_feedback": "",
        "quality_plan": {}, "quality_measurements": {},
        "test_pass_rate": 0, "test_coverage": 0,
        "test_total": 0, "test_passed": 0, "test_smells": 0, "test_flaky": False,
        "correct": False,
        "iteration": 0, "max_iterations": max_iterations, "total_tokens": 0,
        "ai_dead_code": 0, "ai_hallucinated_imports": 0, "ai_duplicates": 0,
        "time_coding": 0, "time_quality": 0, "time_test": 0, "time_correctness": 0,
    }


def run_workflow(name, builder, state):
    start = time.time()
    try:
        wf = builder()
        result = wf.invoke(state)
        elapsed = round(time.time() - start, 1)
        return {
            "workflow": name, "task_id": result["task_id"],
            "iterations": result["iteration"], "correct": result["correct"],
            "quality_verdict": result["quality_verdict"],
            "quality_score": result["quality_score"],
            "test_pass_rate": result["test_pass_rate"],
            "test_passed": result["test_passed"], "test_total": result["test_total"],
            "test_coverage": result["test_coverage"],
            "test_smells": result.get("test_smells", 0),
            "ai_dead_code": result.get("ai_dead_code", 0),
            "ai_hallucinated_imports": result.get("ai_hallucinated_imports", 0),
            "ai_duplicates": result.get("ai_duplicates", 0),
            "time_seconds": elapsed,
            "time_coding": result.get("time_coding", 0),
            "time_quality": result.get("time_quality", 0),
            "time_test": result.get("time_test", 0),
            "time_correctness": result.get("time_correctness", 0),
            "error": None,
        }
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        print(f"  ERROR in {name}: {e}")
        return {
            "workflow": name, "task_id": state["task_id"],
            "iterations": state.get("iteration", 0), "correct": False,
            "quality_verdict": "ERROR", "quality_score": 0,
            "test_pass_rate": 0, "test_passed": 0, "test_total": 0,
            "test_coverage": 0, "test_smells": 0,
            "ai_dead_code": 0, "ai_hallucinated_imports": 0, "ai_duplicates": 0,
            "time_seconds": elapsed,
            "time_coding": 0, "time_quality": 0, "time_test": 0, "time_correctness": 0,
            "error": str(e),
        }


def run_experiment(task_ids, max_iterations=3):
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
            print(f"  Result: correct={result['correct']}, quality={result['quality_verdict']}({result['quality_score']}), tests={result['test_passed']}/{result['test_total']}, time={result['time_seconds']}s [code={result['time_coding']}s, quality={result['time_quality']}s, test={result['time_test']}s]")

    return all_results


def print_summary(results):
    tasks = sorted(set(r["task_id"] for r in results))
    workflows = sorted(set(r["workflow"] for r in results))

    print(f"\n\n{'='*90}")
    print(f"EXPERIMENT SUMMARY")
    print(f"{'='*90}")

    for task in tasks:
        print(f"\n{task}:")
        print(f"  {'Workflow':<18} {'Correct':<9} {'Quality':<14} {'Tests':<10} {'Time':<8} {'Code':<8} {'Qual':<8} {'Test':<8}")
        print(f"  {'-'*82}")
        for wf in workflows:
            r = [x for x in results if x["task_id"] == task and x["workflow"] == wf]
            if r:
                r = r[0]
                q = f"{r['quality_verdict']}({r['quality_score']})"
                t = f"{r['test_passed']}/{r['test_total']}"
                print(f"  {wf:<18} {str(r['correct']):<9} {q:<14} {t:<10} {r['time_seconds']:<8} {r['time_coding']:<8} {r['time_quality']:<8} {r['time_test']:<8}")

    print(f"\n\nAGGREGATE:")
    print(f"  {'Workflow':<18} {'Correct%':<10} {'AvgQual':<10} {'AvgTest':<10} {'AvgTime':<10} {'AvgCode':<10} {'AvgQual':<10} {'AvgTest':<10}")
    print(f"  {'-'*85}")
    for wf in workflows:
        wr = [r for r in results if r["workflow"] == wf]
        n = len(wr)
        if n > 0:
            cp = round(sum(1 for r in wr if r["correct"]) / n * 100, 1)
            aq = round(sum(r["quality_score"] for r in wr) / n, 1)
            at = round(sum(r["test_pass_rate"] for r in wr) / n, 2)
            atime = round(sum(r["time_seconds"] for r in wr) / n, 1)
            ac = round(sum(r["time_coding"] for r in wr) / n, 1)
            aqt = round(sum(r["time_quality"] for r in wr) / n, 1)
            att = round(sum(r["time_test"] for r in wr) / n, 1)
            print(f"  {wf:<18} {cp:<10} {aq:<10} {at:<10} {atime:<10} {ac:<10} {aqt:<10} {att:<10}")
