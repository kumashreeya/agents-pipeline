"""Test that feedback loop actually improves code."""
from human_eval.data import read_problems
from workflows.workflow_c import build_workflow_c

problems = read_problems()
task_id = "HumanEval/3"
problem = problems[task_id]

state = {
    "task_id": task_id,
    "prompt": problem["prompt"],
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

print("Testing Workflow C with improved feedback loop")
print("Watch for: [CODING] Repairing based on feedback...")
print()

wf = build_workflow_c()
result = wf.invoke(state)

print()
print("=" * 60)
print("FINAL RESULT")
print("=" * 60)
print(f"  Iterations: {result['iteration']}")
print(f"  Correct: {result['correct']}")
print(f"  Quality: {result['quality_verdict']} ({result['quality_score']}/100)")
print(f"  Tests: {result['test_passed']}/{result['test_total']}")
