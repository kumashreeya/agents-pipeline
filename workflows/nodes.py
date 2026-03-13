"""
Workflow nodes. Each node is a function that takes state and returns updated state.
These nodes are shared across all 3 workflow variants.
"""
import os
import time
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent
from agents.test_agent import TestAgent


# Create agents once
_coder = CodingAgent()
_quality = QualityAgent()
_tester = TestAgent()


def coding_node(state):
    """Generate or repair code."""
    iteration = state.get("iteration", 0) + 1
    print(f"\n  [CODING] Iteration {iteration}")
    
    prompt = state["prompt"]
    task_id = state["task_id"]
    
    # If we have feedback from previous iteration, include it
    feedback = state.get("quality_feedback", "") or ""
    if feedback and iteration > 1:
        enhanced_prompt = f"{prompt}\n\n# FEEDBACK FROM PREVIOUS ATTEMPT:\n# {feedback}\n"
    else:
        enhanced_prompt = prompt
    
    result = _coder.generate_and_save(task_id, enhanced_prompt)
    
    code = result["full_code"]
    code_file = result["code_file"]
    
    # Syntax check
    try:
        compile(code, code_file, "exec")
        syntax_valid = True
    except SyntaxError:
        syntax_valid = False
    
    print(f"  [CODING] Generated {len(code.split(chr(10)))} lines, syntax={'OK' if syntax_valid else 'ERROR'}")
    
    return {
        **state,
        "code": code,
        "code_file": code_file,
        "syntax_valid": syntax_valid,
        "iteration": iteration,
    }


def quality_node(state):
    """Run quality agent on generated code."""
    print(f"\n  [QUALITY] Evaluating...")
    
    if not state.get("syntax_valid", False):
        print(f"  [QUALITY] Skipped — syntax error")
        return {
            **state,
            "quality_verdict": "SKIP",
            "quality_score": 0,
            "quality_feedback": "Code has syntax errors. Fix syntax first.",
        }
    
    result = _quality.run(state["code_file"])
    
    judgment = result.get("judgment", {})
    verdict = judgment.get("verdict", "UNKNOWN")
    score = judgment.get("quality_score", 0)
    feedback = judgment.get("feedback", "")
    
    # Try to convert score to int
    try:
        score = int(score)
    except (ValueError, TypeError):
        score = 0
    
    print(f"  [QUALITY] Verdict={verdict}, Score={score}/100")
    
    return {
        **state,
        "quality_verdict": verdict,
        "quality_score": score,
        "quality_feedback": feedback,
        "quality_plan": result.get("plan", {}),
        "quality_measurements": result.get("measurements", {}),
    }


def test_node(state):
    """Run test agent on generated code."""
    print(f"\n  [TEST] Generating and running tests...")
    
    if not state.get("syntax_valid", False):
        print(f"  [TEST] Skipped — syntax error")
        return {
            **state,
            "test_pass_rate": 0,
            "test_coverage": 0,
            "test_total": 0,
            "test_passed": 0,
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
    
    pass_rate = pr.get("pass_rate", 0)
    coverage = cov.get("coverage_percent", 0)
    total = pr.get("total", 0)
    passed = pr.get("passed", 0)
    
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
    """Check against HumanEval tests."""
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
    except Exception as e:
        correct = False
    
    print(f"  [CORRECTNESS] {'PASS' if correct else 'FAIL'}")
    
    return {**state, "correct": correct}
