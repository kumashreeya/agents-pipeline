"""Workflow nodes with proper feedback loop."""
import os
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent
from agents.test_agent import TestAgent
from tools.ai_specific_metrics import run_all_ai_metrics

_coder = CodingAgent()
_quality = QualityAgent()
_tester = TestAgent()


def coding_node(state):
    iteration = state.get("iteration", 0) + 1
    print(f"\n  [CODING] Iteration {iteration}")

    task_id = state["task_id"]
    prompt = state["prompt"]
    feedback = state.get("quality_feedback", "") or ""
    previous_code = state.get("code", "") or ""

    # Use feedback if this is a retry
    if iteration > 1 and feedback:
        print(f"  [CODING] Repairing based on feedback: {feedback[:80]}...")
        result = _coder.generate_and_save(
            task_id, prompt,
            feedback=feedback,
            previous_code=previous_code,
            iteration=iteration
        )
    else:
        result = _coder.generate_and_save(task_id, prompt, iteration=iteration)

    code = result["full_code"]
    code_file = result["code_file"]

    try:
        compile(code, code_file, "exec")
        syntax_valid = True
    except SyntaxError:
        syntax_valid = False

    # AI-specific metrics
    ai_metrics = run_all_ai_metrics(code_file)
    dead = ai_metrics["dead_code"]["total"]
    halluc = ai_metrics["hallucinated_imports"]["total"]
    dups = ai_metrics["code_duplication"]["duplicate_functions"]

    print(f"  [CODING] {len(code.split(chr(10)))} lines, syntax={'OK' if syntax_valid else 'ERROR'}, dead={dead}, halluc={halluc}, dups={dups}")

    return {
        **state,
        "code": code,
        "code_file": code_file,
        "syntax_valid": syntax_valid,
        "iteration": iteration,
        "ai_dead_code": dead,
        "ai_hallucinated_imports": halluc,
        "ai_duplicates": dups,
    }


def quality_node(state):
    print(f"\n  [QUALITY] Evaluating...")

    if not state.get("syntax_valid", False):
        print(f"  [QUALITY] Skipped — syntax error")
        return {
            **state,
            "quality_verdict": "SKIP",
            "quality_score": 0,
            "quality_feedback": "Code has syntax errors. Fix the syntax first.",
        }

    result = _quality.run(state["code_file"])
    judgment = result.get("judgment", {})
    verdict = judgment.get("verdict", "UNKNOWN")
    score = judgment.get("quality_score", 0)

    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 0

    # Build specific feedback from metric judgments
    feedback_parts = []
    for mj in judgment.get("metric_judgments", []):
        if mj.get("result") == "FAIL":
            feedback_parts.append(f"- {mj.get('metric', '?')}: {mj.get('explanation', '?')}")

    if judgment.get("top_issues"):
        for issue in judgment["top_issues"][:3]:
            feedback_parts.append(f"- Fix: {issue}")

    if judgment.get("feedback"):
        feedback_parts.append(f"- {judgment['feedback']}")

    specific_feedback = '\n'.join(feedback_parts) if feedback_parts else "Improve overall code quality."

    print(f"  [QUALITY] Verdict={verdict}, Score={score}/100")
    if feedback_parts:
        print(f"  [QUALITY] Feedback: {specific_feedback[:100]}...")

    return {
        **state,
        "quality_verdict": verdict,
        "quality_score": score,
        "quality_feedback": specific_feedback,
        "quality_plan": result.get("plan", {}),
        "quality_measurements": result.get("measurements", {}),
    }


def test_node(state):
    print(f"\n  [TEST] Generating and running tests...")

    if not state.get("syntax_valid", False):
        print(f"  [TEST] Skipped — syntax error")
        return {
            **state,
            "test_pass_rate": 0, "test_coverage": 0,
            "test_total": 0, "test_passed": 0,
        }

    result = _tester.run(
        state["code_file"],
        state["task_id"],
        function_name=state.get("entry_point"),
    )

    metrics = result.get("metrics", {})
    pr = metrics.get("pass_rate", {})
    cov = metrics.get("coverage", {})
    smells = metrics.get("smells", {})
    flaky = metrics.get("flakiness", {})

    passed = pr.get("passed", 0)
    total = pr.get("total", 0)
    pass_rate = pr.get("pass_rate", 0)
    coverage = cov.get("coverage_percent", 0)

    # Build test feedback for retry
    if pass_rate < 0.8 and total > 0:
        test_feedback = f"Tests: {passed}/{total} passed. "
        if pr.get("output"):
            # Extract failure info
            lines = pr["output"].split('\n')
            failures = [l for l in lines if 'FAILED' in l or 'Error' in l]
            if failures:
                test_feedback += "Failures: " + "; ".join(failures[:3])
        state["quality_feedback"] = test_feedback

    print(f"  [TEST] {passed}/{total} passed, coverage={coverage}%")

    return {
        **state,
        "test_pass_rate": pass_rate,
        "test_coverage": coverage,
        "test_total": total,
        "test_passed": passed,
        "test_smells": smells.get("total_smells", 0),
        "test_flaky": flaky.get("is_flaky", False),
    }


def correctness_node(state):
    print(f"\n  [CORRECTNESS] Running HumanEval tests...")

    if not state.get("syntax_valid", False):
        print(f"  [CORRECTNESS] Skipped — syntax error")
        return {**state, "correct": False}

    from human_eval.data import read_problems
    problems = read_problems()
    problem = problems[state["task_id"]]

    try:
        exec_globals = {}
        exec(state["code"], exec_globals)
        check_code = problem["test"] + f"\ncheck({state['entry_point']})"
        exec(check_code, exec_globals)
        correct = True
    except Exception:
        correct = False

    print(f"  [CORRECTNESS] {'PASS' if correct else 'FAIL'}")
    return {**state, "correct": correct}
