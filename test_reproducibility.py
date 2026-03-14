"""
Reproducibility verification: same input must produce same output.
This proves temperature=0 works across the full pipeline.
"""
import json
import time
from human_eval.data import read_problems
from workflows.workflow_a import build_workflow_a
from workflows.workflow_b import build_workflow_b
from workflows.workflow_c import build_workflow_c


def make_state(task_id, problem, max_iter=3):
    return {
        "task_id": task_id, "prompt": problem["prompt"],
        "entry_point": problem["entry_point"],
        "code": "", "code_file": "", "syntax_valid": False,
        "quality_verdict": "", "quality_score": 0, "quality_feedback": "",
        "quality_plan": {}, "quality_measurements": {},
        "test_pass_rate": 0, "test_coverage": 0,
        "test_total": 0, "test_passed": 0, "test_smells": 0, "test_flaky": False,
        "correct": False,
        "iteration": 0, "max_iterations": max_iter, "total_tokens": 0,
        "ai_dead_code": 0, "ai_hallucinated_imports": 0, "ai_duplicates": 0,
    }


def extract_key_results(result):
    """Extract the fields that should be identical across runs."""
    return {
        "correct": result["correct"],
        "quality_verdict": result["quality_verdict"],
        "quality_score": result["quality_score"],
        "test_passed": result["test_passed"],
        "test_total": result["test_total"],
        "test_coverage": result["test_coverage"],
        "iteration": result["iteration"],
        "code": result["code"],
    }


problems = read_problems()
task_ids = ["HumanEval/0", "HumanEval/1", "HumanEval/2"]
workflows = [
    ("A_sequential", build_workflow_a),
    ("B_iterative", build_workflow_b),
    ("C_gated", build_workflow_c),
]

RUNS = 2
all_results = {}
reproducible_count = 0
total_checks = 0

for task_id in task_ids:
    problem = problems[task_id]
    for wf_name, wf_builder in workflows:
        key = f"{task_id}_{wf_name}"
        runs = []

        print(f"\n{task_id} / {wf_name}:")
        for run_num in range(RUNS):
            print(f"  Run {run_num + 1}...", end=" ")
            state = make_state(task_id, problem)
            wf = wf_builder()
            result = wf.invoke(state)
            runs.append(extract_key_results(result))
            print(f"correct={result['correct']}, quality={result['quality_verdict']}({result['quality_score']}), tests={result['test_passed']}/{result['test_total']}")

        # Compare runs
        total_checks += 1
        code_match = runs[0]["code"] == runs[1]["code"]
        correct_match = runs[0]["correct"] == runs[1]["correct"]
        quality_match = runs[0]["quality_verdict"] == runs[1]["quality_verdict"]
        score_match = runs[0]["quality_score"] == runs[1]["quality_score"]
        test_match = runs[0]["test_passed"] == runs[1]["test_passed"]

        all_match = code_match and correct_match and quality_match and score_match and test_match

        if all_match:
            reproducible_count += 1
            print(f"  REPRODUCIBLE: all fields match")
        else:
            print(f"  DIFFERS:")
            if not code_match: print(f"    Code: DIFFERENT")
            if not correct_match: print(f"    Correct: {runs[0]['correct']} vs {runs[1]['correct']}")
            if not quality_match: print(f"    Quality: {runs[0]['quality_verdict']} vs {runs[1]['quality_verdict']}")
            if not score_match: print(f"    Score: {runs[0]['quality_score']} vs {runs[1]['quality_score']}")
            if not test_match: print(f"    Tests: {runs[0]['test_passed']}/{runs[0]['test_total']} vs {runs[1]['test_passed']}/{runs[1]['test_total']}")

print(f"\n{'='*60}")
print(f"REPRODUCIBILITY SUMMARY")
print(f"{'='*60}")
print(f"  Total checks: {total_checks}")
print(f"  Reproducible: {reproducible_count}/{total_checks} ({round(reproducible_count/total_checks*100)}%)")
print(f"  Temperature: 0 (deterministic)")
