"""
Fixed Baseline Quality Check - no AI decisions.
"""
import json
import datetime
from tools.metric_runners import ALL_METRICS, run_metric

FIXED_THRESHOLDS = {
    "lint_violations": {"metric": "lint_violations", "threshold": 5, "comparison": "<=", "field": "total", "description": "Max 5 lint violations"},
    "security_vulnerabilities": {"metric": "security_vulnerabilities", "threshold": 0, "comparison": "==", "field": "high", "description": "Zero HIGH severity"},
    "cyclomatic_complexity": {"metric": "cyclomatic_complexity", "threshold": 10, "comparison": "<=", "field": "average", "description": "Avg complexity <= 10"},
    "maintainability_index": {"metric": "maintainability_index", "threshold": 20, "comparison": ">=", "field": "score", "description": "MI score >= 20"},
    "type_errors": {"metric": "type_errors", "threshold": 5, "comparison": "<=", "field": "total_errors", "description": "Max 5 type errors"},
    "halstead_difficulty": {"metric": "halstead_difficulty", "threshold": 30, "comparison": "<=", "field": "difficulty", "description": "Difficulty <= 30"},
    "sloc": {"metric": "sloc", "threshold": 200, "comparison": "<=", "field": "sloc", "description": "SLOC <= 200"},
}

def run_baseline(code_file):
    measurements = {}
    for name in ALL_METRICS:
        measurements[name] = run_metric(name, code_file)
    judgments = {}
    for name, info in FIXED_THRESHOLDS.items():
        if name in measurements:
            value = measurements[name].get(info["field"], 0)
            comp = info["comparison"]
            thresh = info["threshold"]
            if comp == "<=": passed = value <= thresh
            elif comp == ">=": passed = value >= thresh
            elif comp == "==": passed = value == thresh
            else: passed = True
            judgments[name] = {"metric": name, "measured_value": value, "threshold": thresh, "comparison": comp, "result": "PASS" if passed else "FAIL", "description": info["description"]}
    failed = [j for j in judgments.values() if j["result"] == "FAIL"]
    critical = [j for j in failed if j["metric"] == "security_vulnerabilities"]
    if critical: verdict = "FAIL"
    elif len(failed) >= 3: verdict = "FAIL"
    elif len(failed) >= 1: verdict = "NEEDS_IMPROVEMENT"
    else: verdict = "PASS"
    total = len(judgments)
    pc = total - len(failed)
    return {"timestamp": datetime.datetime.now().isoformat(), "code_file": code_file, "type": "fixed_baseline", "measurements": measurements, "judgments": judgments, "verdict": verdict, "quality_score": round((pc / total) * 100) if total > 0 else 0, "passed_count": pc, "failed_count": len(failed), "failed_metrics": [j["metric"] for j in failed]}

def compare_with_agent(baseline_result, agent_result):
    agent_plan = agent_result.get("plan", {})
    agent_selected = [m.get("metric") for m in agent_plan.get("selected_metrics", [])]
    baseline_judgments = baseline_result.get("judgments", {})
    analysis = {"correct_selections": [], "correct_skips": [], "missed_failures": [], "unnecessary_selections": []}
    for mn, jd in baseline_judgments.items():
        sel = mn in agent_selected
        bp = jd["result"] == "PASS"
        if sel and not bp: analysis["correct_selections"].append({"metric": mn, "reason": "Agent correctly selected - FAILED baseline"})
        elif sel and bp: analysis["unnecessary_selections"].append({"metric": mn, "reason": "Agent selected but PASSED easily"})
        elif not sel and not bp: analysis["missed_failures"].append({"metric": mn, "reason": "Agent SKIPPED but FAILED baseline"})
        elif not sel and bp: analysis["correct_skips"].append({"metric": mn, "reason": "Agent correctly skipped - PASSED"})
    total = len(baseline_judgments)
    correct = len(analysis["correct_selections"]) + len(analysis["correct_skips"])
    analysis["agreement_rate"] = round(correct / total * 100, 1) if total > 0 else 0
    av = agent_result.get("judgment", {}).get("verdict", "UNKNOWN")
    bv = baseline_result.get("verdict", "UNKNOWN")
    return {"agent_selected": agent_selected, "baseline_failed_metrics": baseline_result.get("failed_metrics", []), "analysis": analysis, "verdict_comparison": {"agent_verdict": av, "baseline_verdict": bv, "agree": av == bv}}
