"""Workflow nodes with timing and token counting."""
import os
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent
from agents.test_agent import TestAgent
from tools.ai_specific_metrics import run_all_ai_metrics
from tools.timer import timer

_coder = CodingAgent()
_quality = QualityAgent()
_tester = TestAgent()


def coding_node(state):
    timer.start('coding')
    iteration = state.get("iteration", 0) + 1
    print(f"\n  [CODING] Iteration {iteration}")

    task_id = state["task_id"]
    prompt = state["prompt"]
    feedback = state.get("quality_feedback", "") or ""
    previous_code = state.get("code", "") or ""

    if iteration > 1 and feedback:
        print(f"  [CODING] Repairing: {feedback[:80]}...")
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

    ai_metrics = run_all_ai_metrics(code_file)
    dead = ai_metrics["dead_code"]["total"]
    halluc = ai_metrics["hallucinated_imports"]["total"]
    dups = ai_metrics["code_duplication"]["duplicate_functions"]

    timer.stop('coding')
    print(f"  [CODING] {len(code.split(chr(10)))} lines, syntax={'OK' if syntax_valid else 'ERROR'}, dead={dead}, halluc={halluc}, dups={dups} ({timer.get('coding')}s)")

    # Accumulate timing
    prev_coding_time = state.get("time_coding", 0)

    return {
        **state,
        "code": code,
        "code_file": code_file,
        "syntax_valid": syntax_valid,
        "iteration": iteration,
        "ai_dead_code": dead,
        "ai_hallucinated_imports": halluc,
        "ai_duplicates": dups,
        "time_coding": round(prev_coding_time + timer.get('coding'), 2),
    }


def quality_node(state):
    timer.start('quality')
    print(f"\n  [QUALITY] Evaluating...")

    if not state.get("syntax_valid", False):
        timer.stop('quality')
        print(f"  [QUALITY] Skipped — syntax error")
        return {
            **state,
            "quality_verdict": "SKIP",
            "quality_score": 0,
            "quality_feedback": "Code has syntax errors. Fix the syntax first.",
            "time_quality": round(state.get("time_quality", 0) + timer.get('quality'), 2),
        }

    result = _quality.run(state["code_file"])
    judgment = result.get("judgment", {})
    verdict = judgment.get("verdict", "UNKNOWN")
    score = judgment.get("quality_score", 0)

    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 0

    feedback_parts = []
    for mj in judgment.get("metric_judgments", []):
        if mj.get("result") == "FAIL":
            feedback_parts.append(f"- {mj.get('metric')}: measured {mj.get('measured_value')}, need {mj.get('comparison')}{mj.get('threshold')}")

    if judgment.get("feedback"):
        feedback_parts.append(f"- {judgment['feedback']}")

    specific_feedback = '\n'.join(feedback_parts) if feedback_parts else "Improve overall code quality."

    timer.stop('quality')
    print(f"  [QUALITY] Verdict={verdict}, Score={score}/100 ({timer.get('quality')}s)")

    return {
        **state,
        "quality_verdict": verdict,
        "quality_score": score,
        "quality_feedback": specific_feedback,
        "quality_plan": result.get("plan", {}),
        "quality_measurements": result.get("measurements", {}),
        "time_quality": round(state.get("time_quality", 0) + timer.get('quality'), 2),
    }


def test_node(state):
    timer.start('test')
    print(f"\n  [TEST] Generating and running tests...")

    if not state.get("syntax_valid", False):
        timer.stop('test')
        print(f"  [TEST] Skipped — syntax error")
        return {
            **state,
            "test_pass_rate": 0, "test_coverage": 0,
            "test_total": 0, "test_passed": 0,
            "time_test": round(state.get("time_test", 0) + timer.get('test'), 2),
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

    if pass_rate < 0.8 and total > 0:
        test_feedback = f"Tests: {passed}/{total} passed."
        if pr.get("output"):
            failures = [l for l in pr["output"].split('\n') if 'FAILED' in l or 'Error' in l]
            if failures:
                test_feedback += " Failures: " + "; ".join(failures[:3])
        state = {**state, "quality_feedback": test_feedback}

    timer.stop('test')
    print(f"  [TEST] {passed}/{total} passed, coverage={coverage}% ({timer.get('test')}s)")

    return {
        **state,
        "test_pass_rate": pass_rate,
        "test_coverage": coverage,
        "test_total": total,
        "test_passed": passed,
        "test_smells": smells.get("total_smells", 0),
        "test_flaky": flaky.get("is_flaky", False),
        "time_test": round(state.get("time_test", 0) + timer.get('test'), 2),
    }


def correctness_node(state):
    timer.start('correctness')
    print(f"\n  [CORRECTNESS] Running HumanEval tests...")

    if not state.get("syntax_valid", False):
        timer.stop('correctness')
        return {**state, "correct": False, "time_correctness": timer.get('correctness')}

    from human_eval.data import read_problems
    problems = read_problems()
    problem = problems[state["task_id"]]

    try:
        exec_globals = {}
        exec(state["code"], exec_globals)
        check_code = problem["test"] + f"\ncheck({state['entry_point']})"
        exec(check_code, exec_globals)
        correct = True
    except Exception as e:
        correct = False
        error_msg = str(e)[:200]
        state = {**state, "quality_feedback": f"Code fails HumanEval tests: {error_msg}"}

    timer.stop('correctness')
    print(f"  [CORRECTNESS] {'PASS' if correct else 'FAIL'} ({timer.get('correctness')}s)")
    return {**state, "correct": correct, "time_correctness": timer.get('correctness')}


def quick_correctness_node(state):
    timer.start('quick_check')
    print(f"\n  [QUICK CHECK] Testing correctness...")

    if not state.get("syntax_valid", False):
        timer.stop('quick_check')
        return {**state, "correct": False, "quality_feedback": "Code has syntax errors."}

    from human_eval.data import read_problems
    problems = read_problems()
    problem = problems[state["task_id"]]

    try:
        exec_globals = {}
        exec(state["code"], exec_globals)
        check_code = problem["test"] + f"\ncheck({state['entry_point']})"
        exec(check_code, exec_globals)
        correct = True
        timer.stop('quick_check')
        print(f"  [QUICK CHECK] PASS ({timer.get('quick_check')}s)")
    except Exception as e:
        correct = False
        error_msg = str(e)[:200]
        timer.stop('quick_check')
        print(f"  [QUICK CHECK] FAIL ({timer.get('quick_check')}s)")
        state = {**state, "quality_feedback": f"Code produces wrong output: {error_msg}"}

    return {**state, "correct": correct}
