"""Compare agent vs baseline on 3 HumanEval problems."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent
from tools.baseline_quality import run_baseline, compare_with_agent

problems = read_problems()
coder = CodingAgent()
quality = QualityAgent()

task_ids = ["HumanEval/0", "HumanEval/1", "HumanEval/2"]
all_results = []

for task_id in task_ids:
    problem = problems[task_id]
    print()
    print("=" * 60)
    print("TASK:", task_id)
    print("=" * 60)

    code_result = coder.generate_and_save(task_id, problem["prompt"])
    baseline = run_baseline(code_result["code_file"])
    agent_result = quality.run(code_result["code_file"])
    comp = compare_with_agent(baseline, agent_result)

    all_results.append({
        "task": task_id,
        "baseline_verdict": baseline["verdict"],
        "baseline_score": baseline["quality_score"],
        "baseline_failed": baseline["failed_metrics"],
        "agent_verdict": agent_result["judgment"].get("verdict", "?"),
        "agent_score": agent_result["judgment"].get("quality_score", "?"),
        "agent_selected": comp["agent_selected"],
        "agreement": comp["analysis"]["agreement_rate"],
        "missed": [m["metric"] for m in comp["analysis"]["missed_failures"]],
    })

    print(f"  Baseline: {baseline['verdict']} ({baseline['quality_score']}/100)")
    print(f"  Agent:    {agent_result['judgment'].get('verdict','?')} ({agent_result['judgment'].get('quality_score','?')}/100)")
    print(f"  Agree:    {comp['verdict_comparison']['agree']}")
    print(f"  Rate:     {comp['analysis']['agreement_rate']}%")
    if comp["analysis"]["missed_failures"]:
        print(f"  MISSED:   {[m['metric'] for m in comp['analysis']['missed_failures']]}")

print()
print("=" * 60)
print("SUMMARY TABLE")
print("=" * 60)
print(f"{'Task':<15} {'Baseline':<12} {'Agent':<12} {'Agree%':<10} {'Missed'}")
print("-" * 65)
for r in all_results:
    print(f"{r['task']:<15} {r['baseline_verdict']:<12} {r['agent_verdict']:<12} {r['agreement']:<10} {r['missed']}")
