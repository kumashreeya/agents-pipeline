"""Test improved workflows — B now uses correctness checking."""
import time
from human_eval.data import read_problems
from workflows.workflow_a import build_workflow_a
from workflows.workflow_b import build_workflow_b
from workflows.workflow_c import build_workflow_c

problems = read_problems()
task_id = "HumanEval/3"
problem = problems[task_id]

state = {
    "task_id": task_id, "prompt": problem["prompt"],
    "entry_point": problem["entry_point"],
    "code": "", "code_file": "", "syntax_valid": False,
    "quality_verdict": "", "quality_score": 0, "quality_feedback": "",
    "quality_plan": {}, "quality_measurements": {},
    "test_pass_rate": 0, "test_coverage": 0,
    "test_total": 0, "test_passed": 0, "test_smells": 0, "test_flaky": False,
    "correct": False,
    "iteration": 0, "max_iterations": 3, "total_tokens": 0,
    "ai_dead_code": 0, "ai_hallucinated_imports": 0, "ai_duplicates": 0,
}

for name, builder in [("A_sequential", build_workflow_a), ("B_iterative", build_workflow_b), ("C_gated", build_workflow_c)]:
    print(f"\n{'='*60}")
    print(f"WORKFLOW: {name}")
    print(f"{'='*60}")

    start = time.time()
    wf = builder()
    result = wf.invoke(dict(state))
    elapsed = round(time.time() - start, 1)

    print(f"\n  Result: correct={result['correct']}, quality={result['quality_verdict']}({result['quality_score']}), tests={result['test_passed']}/{result['test_total']}, iters={result['iteration']}, time={elapsed}s")
