"""
Complete Pipeline: Coding Agent -> Quality Agent -> Test Agent
This runs all three agents on a HumanEval problem and collects all metrics.
"""
import json
import datetime
import os
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent
from agents.test_agent import TestAgent


def run_pipeline(task_id, problem, output_dir='results'):
    """Run the complete evaluation pipeline on one task."""

    print(f"\n{'='*60}")
    print(f"PIPELINE: {task_id}")
    print(f"{'='*60}")

    coder = CodingAgent()
    quality = QualityAgent()
    tester = TestAgent()

    # ==========================================
    # STEP 1: Generate code
    # ==========================================
    print(f"\n--- STEP 1: Coding Agent ---")
    code_result = coder.generate_and_save(task_id, problem['prompt'], output_dir)
    print(f"  Code saved to: {code_result['code_file']}")

    # Syntax check
    try:
        compile(code_result['full_code'], code_result['code_file'], 'exec')
        syntax_ok = True
        print(f"  Syntax: OK")
    except SyntaxError as e:
        syntax_ok = False
        print(f"  Syntax: FAILED — {e}")

    # ==========================================
    # STEP 2: Quality Agent evaluates code
    # ==========================================
    print(f"\n--- STEP 2: Quality Agent ---")
    if syntax_ok:
        quality_result = quality.run(code_result['code_file'])
        q_judgment = quality_result.get('judgment', {})
        print(f"  Verdict: {q_judgment.get('verdict', '?')}")
        print(f"  Score: {q_judgment.get('quality_score', '?')}/100")
    else:
        quality_result = {'judgment': {'verdict': 'SKIP', 'reason': 'syntax error'}}
        print(f"  Skipped — code has syntax errors")

    # ==========================================
    # STEP 3: Test Agent evaluates code
    # ==========================================
    print(f"\n--- STEP 3: Test Agent ---")
    if syntax_ok:
        test_result = tester.run(
            code_result['code_file'],
            task_id,
            function_name=problem['entry_point'],
            output_dir=output_dir
        )
        t_metrics = test_result.get('metrics', {})
        pr = t_metrics.get('pass_rate', {})
        cov = t_metrics.get('coverage', {})
        print(f"  Tests: {pr.get('passed', 0)}/{pr.get('total', 0)} passed")
        print(f"  Coverage: {cov.get('coverage_percent', 0)}%")
    else:
        test_result = {'metrics': {'error': 'syntax error'}}
        print(f"  Skipped — code has syntax errors")

    # ==========================================
    # STEP 4: Check correctness (HumanEval tests)
    # ==========================================
    print(f"\n--- STEP 4: Correctness Check ---")
    correctness = False
    if syntax_ok:
        try:
            exec_globals = {}
            exec(code_result['full_code'], exec_globals)
            check_code = problem['test'] + f"\ncheck({problem['entry_point']})"
            exec(check_code, exec_globals)
            correctness = True
            print(f"  HumanEval tests: PASSED")
        except Exception as e:
            print(f"  HumanEval tests: FAILED — {str(e)[:100]}")
    else:
        print(f"  Skipped — code has syntax errors")

    # ==========================================
    # COMBINE ALL RESULTS
    # ==========================================
    combined = {
        'timestamp': datetime.datetime.now().isoformat(),
        'task_id': task_id,
        'correctness': correctness,
        'syntax_valid': syntax_ok,
        'quality': {
            'verdict': quality_result.get('judgment', {}).get('verdict', '?'),
            'score': quality_result.get('judgment', {}).get('quality_score', '?'),
            'metrics_checked': [m.get('metric') for m in quality_result.get('plan', {}).get('selected_metrics', [])],
        },
        'testing': {
            'pass_rate': t_metrics.get('pass_rate', {}).get('pass_rate', 0) if syntax_ok else 0,
            'tests_passed': t_metrics.get('pass_rate', {}).get('passed', 0) if syntax_ok else 0,
            'tests_total': t_metrics.get('pass_rate', {}).get('total', 0) if syntax_ok else 0,
            'coverage': t_metrics.get('coverage', {}).get('coverage_percent', 0) if syntax_ok else 0,
            'smells': t_metrics.get('smells', {}).get('total_smells', 0) if syntax_ok else 0,
            'is_flaky': t_metrics.get('flakiness', {}).get('is_flaky', False) if syntax_ok else False,
        },
    }

    # Save combined log
    task_dir = os.path.join(output_dir, task_id.replace('/', '_'))
    os.makedirs(task_dir, exist_ok=True)
    log_file = os.path.join(task_dir, 'pipeline_log.json')
    with open(log_file, 'w') as f:
        json.dump(combined, f, indent=2, default=str)

    return combined


def print_summary(result):
    """Print a clean summary of pipeline results."""
    print(f"\n{'='*60}")
    print(f"PIPELINE SUMMARY: {result['task_id']}")
    print(f"{'='*60}")
    print(f"  Correctness:    {'PASS' if result['correctness'] else 'FAIL'}")
    print(f"  Quality:        {result['quality']['verdict']} ({result['quality']['score']}/100)")
    print(f"  Test Pass Rate: {result['testing']['tests_passed']}/{result['testing']['tests_total']} ({result['testing']['pass_rate']})")
    print(f"  Coverage:       {result['testing']['coverage']}%")
    print(f"  Test Smells:    {result['testing']['smells']}")
    print(f"  Flaky:          {result['testing']['is_flaky']}")
    print(f"  Quality Metrics: {result['quality']['metrics_checked']}")


# ==========================================
# RUN ON MULTIPLE PROBLEMS
# ==========================================
if __name__ == '__main__':
    problems = read_problems()

    # Run on first 3 problems
    task_ids = ["HumanEval/0", "HumanEval/1", "HumanEval/2"]

    all_results = []
    for task_id in task_ids:
        result = run_pipeline(task_id, problems[task_id])
        print_summary(result)
        all_results.append(result)

    # Final summary table
    print(f"\n\n{'='*60}")
    print(f"ALL RESULTS")
    print(f"{'='*60}")
    print(f"{'Task':<15} {'Correct':<10} {'Quality':<12} {'Tests':<12} {'Coverage':<10}")
    print(f"{'-'*60}")
    for r in all_results:
        print(f"{r['task_id']:<15} {'PASS' if r['correctness'] else 'FAIL':<10} {str(r['quality']['verdict']):<12} {r['testing']['tests_passed']}/{r['testing']['tests_total']:<10} {r['testing']['coverage']}%")
