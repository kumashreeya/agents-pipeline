"""
Main entry point for the quality agent.
"""
from agents.quality_agent import QualityAgent


def print_results(result):
    """Pretty print agent results."""
    plan = result['plan']
    judgment = result['judgment']

    print(f"\n  Purpose: {plan.get('code_purpose', '?')}")
    print(f"  Dangerous patterns: {plan.get('dangerous_patterns_found', [])}")
    print(f"  Risk: {plan.get('risk_level', '?')}")

    print(f"\n  Metrics selected:")
    for m in plan.get('selected_metrics', []):
        print(f"    [{m.get('priority', '?')}] {m.get('metric', '?')}")

    print(f"\n  Metrics skipped:")
    for s in plan.get('skipped_metrics', []):
        print(f"    {s.get('metric', '?')}: {s.get('why_skipped', '?')}")

    print(f"\n  {'='*50}")
    print(f"  VERDICT: {judgment.get('verdict', '?')}")
    print(f"  SCORE: {judgment.get('quality_score', '?')}/100")
    print(f"  REASON: {judgment.get('reasoning', '?')}")
    print(f"  {'='*50}")

    if judgment.get('metric_judgments'):
        for mj in judgment['metric_judgments']:
            icon = 'PASS' if mj.get('result') == 'PASS' else 'FAIL'
            print(f"  [{icon}] {mj.get('metric', '?')}: {mj.get('explanation', '?')}")

    if judgment.get('top_issues'):
        print(f"\n  Fix these:")
        for i, issue in enumerate(judgment['top_issues'], 1):
            print(f"    {i}. {issue}")

    if judgment.get('feedback'):
        print(f"\n  Feedback: {judgment['feedback']}")

    print(f"\n  Log saved: logs/")


if __name__ == '__main__':
    agent = QualityAgent()

    print("="*60)
    print("TEST 1: Good code")
    print("="*60)
    result1 = agent.run('sample_code/good_code.py')
    print_results(result1)

    print("\n\n" + "="*60)
    print("TEST 2: Bad code")
    print("="*60)
    result2 = agent.run('sample_code/bad_code.py')
    print_results(result2)
