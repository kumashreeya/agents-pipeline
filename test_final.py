"""Final test: all improvements on one problem."""
import time
from human_eval.data import read_problems
from workflows.workflow_a import build_workflow_a
from workflows.workflow_b import build_workflow_b
from workflows.workflow_c import build_workflow_c
from tools.baseline_quality import run_baseline, compare_with_agent

problems = read_problems()
task_id = "HumanEval/4"
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

results = {}
for name, builder in [("A", build_workflow_a), ("B", build_workflow_b), ("C", build_workflow_c)]:
    print(f"\n{'='*60}")
    print(f"WORKFLOW {name}")
    print(f"{'='*60}")
    start = time.time()
    wf = builder()
    r = wf.invoke(dict(state))
    elapsed = round(time.time() - start, 1)

    # Run baseline comparison
    baseline = run_baseline(r["code_file"]) if r.get("code_file") else None
    agent_result = {"plan": r.get("quality_plan", {}), "judgment": {"verdict": r["quality_verdict"]}}
    comp = compare_with_agent(baseline, agent_result) if baseline else None

    results[name] = r
    results[name]["time"] = elapsed
    results[name]["baseline_verdict"] = baseline["verdict"] if baseline else "N/A"
    results[name]["agreement"] = comp["analysis"]["agreement_rate"] if comp else 0

print(f"\n\n{'='*60}")
print(f"FINAL COMPARISON: {task_id}")
print(f"{'='*60}")
print(f"{'Metric':<22} {'A (Sequential)':<18} {'B (Iterative)':<18} {'C (Gated)'}")
print(f"{'-'*75}")
print(f"{'Correct':<22} {str(results['A']['correct']):<18} {str(results['B']['correct']):<18} {results['C']['correct']}")
print(f"{'Quality Verdict':<22} {results['A']['quality_verdict']:<18} {results['B']['quality_verdict']:<18} {results['C']['quality_verdict']}")
print(f"{'Quality Score':<22} {results['A']['quality_score']:<18} {results['B']['quality_score']:<18} {results['C']['quality_score']}")
print(f"{'Tests Passed':<22} {str(results['A']['test_passed'])+'/'+str(results['A']['test_total']):<18} {str(results['B']['test_passed'])+'/'+str(results['B']['test_total']):<18} {str(results['C']['test_passed'])+'/'+str(results['C']['test_total'])}")
print(f"{'Coverage':<22} {str(results['A']['test_coverage'])+'%':<18} {str(results['B']['test_coverage'])+'%':<18} {str(results['C']['test_coverage'])+'%'}")
print(f"{'Iterations':<22} {results['A']['iteration']:<18} {results['B']['iteration']:<18} {results['C']['iteration']}")
print(f"{'Time':<22} {str(results['A']['time'])+'s':<18} {str(results['B']['time'])+'s':<18} {str(results['C']['time'])+'s'}")
print(f"{'Dead Code':<22} {results['A']['ai_dead_code']:<18} {results['B']['ai_dead_code']:<18} {results['C']['ai_dead_code']}")
print(f"{'Duplicates':<22} {results['A']['ai_duplicates']:<18} {results['B']['ai_duplicates']:<18} {results['C']['ai_duplicates']}")
print(f"{'Baseline Verdict':<22} {results['A']['baseline_verdict']:<18} {results['B']['baseline_verdict']:<18} {results['C']['baseline_verdict']}")
print(f"{'Baseline Agreement':<22} {str(results['A']['agreement'])+'%':<18} {str(results['B']['agreement'])+'%':<18} {str(results['C']['agreement'])+'%'}")
