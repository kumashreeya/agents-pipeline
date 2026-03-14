"""Test hybrid AST + LLM planning."""
from agents.quality_agent import QualityAgent
from tools.baseline_quality import run_baseline, compare_with_agent

quality = QualityAgent()

# Test on good code
print("=" * 60)
print("TEST 1: Simple safe code")
print("=" * 60)
result = quality.run('sample_code/good_code.py')
plan = result['plan']
print(f"  Analysis: loops={plan['code_analysis']['has_loops']}, types={plan['code_analysis']['has_type_hints']}, complex={plan['code_analysis']['is_complex']}")
print(f"  Selected: {[m['metric'] for m in plan['selected_metrics']]}")
print(f"  Skipped:  {[s['metric'] for s in plan['skipped_metrics']]}")
print(f"  Verdict:  {result['judgment']['verdict']} ({result['judgment']['quality_score']}/100)")

# Compare with baseline
baseline = run_baseline('sample_code/good_code.py')
comp = compare_with_agent(baseline, result)
print(f"  Baseline: {baseline['verdict']}")
print(f"  Agree:    {comp['verdict_comparison']['agree']}")
print(f"  Rate:     {comp['analysis']['agreement_rate']}%")

# Test on bad code
print(f"\n{'='*60}")
print("TEST 2: Dangerous code with security risks")
print("=" * 60)
result2 = quality.run('sample_code/bad_code.py')
plan2 = result2['plan']
print(f"  Security patterns: {plan2['dangerous_patterns_found']}")
print(f"  Analysis: loops={plan2['code_analysis']['has_loops']}, complex={plan2['code_analysis']['is_complex']}")
print(f"  Selected: {[m['metric'] for m in plan2['selected_metrics']]}")
print(f"  Skipped:  {[s['metric'] for s in plan2['skipped_metrics']]}")
print(f"  Verdict:  {result2['judgment']['verdict']} ({result2['judgment']['quality_score']}/100)")
if result2['judgment'].get('failed_metrics'):
    print(f"  Failed:   {result2['judgment']['failed_metrics']}")

baseline2 = run_baseline('sample_code/bad_code.py')
comp2 = compare_with_agent(baseline2, result2)
print(f"  Baseline: {baseline2['verdict']}")
print(f"  Agree:    {comp2['verdict_comparison']['agree']}")
print(f"  Rate:     {comp2['analysis']['agreement_rate']}%")
