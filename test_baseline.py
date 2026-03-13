"""Compare autonomous agent vs fixed baseline."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent
from tools.baseline_quality import run_baseline, compare_with_agent

problems = read_problems()
coder = CodingAgent()
quality = QualityAgent()

task_id = "HumanEval/0"
problem = problems[task_id]

print("=" * 60)
print("Generating code for", task_id)
print("=" * 60)
code_result = coder.generate_and_save(task_id, problem["prompt"])
print("  Saved to:", code_result["code_file"])

print()
print("=" * 60)
print("FIXED BASELINE (all 7 metrics, fixed thresholds)")
print("=" * 60)
baseline = run_baseline(code_result["code_file"])

print()
print("  Verdict:", baseline["verdict"])
print("  Score:", baseline["quality_score"], "/100")
print("  Passed:", baseline["passed_count"], "/7")
print("  Failed:", baseline["failed_count"], "/7")
if baseline["failed_metrics"]:
    print("  Failed metrics:", baseline["failed_metrics"])

print()
print("  All results:")
for name, j in baseline["judgments"].items():
    icon = "PASS" if j["result"] == "PASS" else "FAIL"
    print(f"    [{icon}] {name}: {j['measured_value']} (threshold: {j['comparison']}{j['threshold']})")

print()
print("=" * 60)
print("AUTONOMOUS AGENT (selects its own metrics)")
print("=" * 60)
agent_result = quality.run(code_result["code_file"])

plan = agent_result["plan"]
judgment = agent_result["judgment"]
print()
print("  Selected:", [m.get("metric") for m in plan.get("selected_metrics", [])])
print("  Skipped:", [s.get("metric") for s in plan.get("skipped_metrics", [])])
print("  Verdict:", judgment.get("verdict", "?"))
print("  Score:", judgment.get("quality_score", "?"), "/100")

print()
print("=" * 60)
print("COMPARISON: Agent vs Baseline")
print("=" * 60)
comp = compare_with_agent(baseline, agent_result)

print()
print("  Verdicts agree:", comp["verdict_comparison"]["agree"])
print("    Baseline:", comp["verdict_comparison"]["baseline_verdict"])
print("    Agent:   ", comp["verdict_comparison"]["agent_verdict"])
print()
print("  Agreement rate:", comp["analysis"]["agreement_rate"], "%")

if comp["analysis"]["correct_selections"]:
    print()
    print("  CORRECT selections (picked it, it failed):")
    for c in comp["analysis"]["correct_selections"]:
        print("    +", c["metric"])

if comp["analysis"]["correct_skips"]:
    print()
    print("  CORRECT skips (skipped it, it passed):")
    for c in comp["analysis"]["correct_skips"]:
        print("    +", c["metric"])

if comp["analysis"]["missed_failures"]:
    print()
    print("  MISSED FAILURES (skipped it, but it FAILED!):")
    for m in comp["analysis"]["missed_failures"]:
        print("    !!", m["metric"], "-", m["reason"])

if comp["analysis"]["unnecessary_selections"]:
    print()
    print("  Unnecessary (picked it, but passed easily):")
    for u in comp["analysis"]["unnecessary_selections"]:
        print("    ~", u["metric"])
