"""Test all 3 workflow variants on the same HumanEval problem."""
import time
from human_eval.data import read_problems
from workflows.workflow_a import build_workflow_a
from workflows.workflow_b import build_workflow_b
from workflows.workflow_c import build_workflow_c

problems = read_problems()
task_id = "HumanEval/0"
problem = problems[task_id]

# Initial state — same for all workflows
initial_state = {
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
    "max_iterations": 3,
    "total_tokens": 0,
}

results = {}

# ==========================================
# WORKFLOW A: Sequential
# ==========================================
print("=" * 60)
print("WORKFLOW A: Sequential (code -> quality -> test -> correctness)")
print("=" * 60)
start = time.time()
wf_a = build_workflow_a()
result_a = wf_a.invoke(initial_state)
time_a = round(time.time() - start, 1)
results["A"] = result_a
print(f"\n  Time: {time_a}s")
print(f"  Iterations: {result_a['iteration']}")
print(f"  Correct: {result_a['correct']}")
print(f"  Quality: {result_a['quality_verdict']} ({result_a['quality_score']}/100)")
print(f"  Tests: {result_a['test_passed']}/{result_a['test_total']} ({result_a['test_pass_rate']})")
print(f"  Coverage: {result_a['test_coverage']}%")

# ==========================================
# WORKFLOW B: Iterative
# ==========================================
print("\n" + "=" * 60)
print("WORKFLOW B: Iterative (code -> test -> [retry] -> quality -> correctness)")
print("=" * 60)
start = time.time()
wf_b = build_workflow_b()
result_b = wf_b.invoke(initial_state)
time_b = round(time.time() - start, 1)
results["B"] = result_b
print(f"\n  Time: {time_b}s")
print(f"  Iterations: {result_b['iteration']}")
print(f"  Correct: {result_b['correct']}")
print(f"  Quality: {result_b['quality_verdict']} ({result_b['quality_score']}/100)")
print(f"  Tests: {result_b['test_passed']}/{result_b['test_total']} ({result_b['test_pass_rate']})")
print(f"  Coverage: {result_b['test_coverage']}%")

# ==========================================
# WORKFLOW C: Early-Gated
# ==========================================
print("\n" + "=" * 60)
print("WORKFLOW C: Early-Gated (code -> quality -> [retry] -> test -> correctness)")
print("=" * 60)
start = time.time()
wf_c = build_workflow_c()
result_c = wf_c.invoke(initial_state)
time_c = round(time.time() - start, 1)
results["C"] = result_c
print(f"\n  Time: {time_c}s")
print(f"  Iterations: {result_c['iteration']}")
print(f"  Correct: {result_c['correct']}")
print(f"  Quality: {result_c['quality_verdict']} ({result_c['quality_score']}/100)")
print(f"  Tests: {result_c['test_passed']}/{result_c['test_total']} ({result_c['test_pass_rate']})")
print(f"  Coverage: {result_c['test_coverage']}%")

# ==========================================
# COMPARISON TABLE
# ==========================================
print("\n" + "=" * 60)
print("WORKFLOW COMPARISON")
print("=" * 60)
print(f"{'Metric':<20} {'A (Sequential)':<18} {'B (Iterative)':<18} {'C (Gated)':<18}")
print("-" * 74)
print(f"{'Iterations':<20} {results['A']['iteration']:<18} {results['B']['iteration']:<18} {results['C']['iteration']:<18}")
print(f"{'Correct':<20} {str(results['A']['correct']):<18} {str(results['B']['correct']):<18} {str(results['C']['correct']):<18}")
print(f"{'Quality':<20} {results['A']['quality_verdict']:<18} {results['B']['quality_verdict']:<18} {results['C']['quality_verdict']:<18}")
print(f"{'Quality Score':<20} {results['A']['quality_score']:<18} {results['B']['quality_score']:<18} {results['C']['quality_score']:<18}")
print(f"{'Test Pass Rate':<20} {results['A']['test_pass_rate']:<18} {results['B']['test_pass_rate']:<18} {results['C']['test_pass_rate']:<18}")
print(f"{'Coverage':<20} {results['A']['test_coverage']:<18} {results['B']['test_coverage']:<18} {results['C']['test_coverage']:<18}")
print(f"{'Time (s)':<20} {time_a:<18} {time_b:<18} {time_c:<18}")
