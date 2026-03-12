"""Test the full pipeline: Coding Agent -> Test Agent with correct paths."""
import subprocess
import os
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.test_agent import TestAgent

problems = read_problems()
coder = CodingAgent()
tester = TestAgent()

task_id = "HumanEval/0"
problem = problems[task_id]

# Step 1: Generate code
print(f"{'='*60}")
print(f"CODING AGENT: Generating code for {task_id}")
print(f"{'='*60}")
code_result = coder.generate_and_save(task_id, problem['prompt'])
print(f"  Saved to: {code_result['code_file']}")

# Step 2: Run pytest manually to verify it works
print(f"\n{'='*60}")
print(f"MANUAL PYTEST CHECK")
print(f"{'='*60}")
task_dir = os.path.dirname(code_result['code_file'])
test_file = os.path.join(task_dir, 'generated_tests.py')

if os.path.exists(test_file):
    result = subprocess.run(
        ['python', '-m', 'pytest', 'generated_tests.py', '-v'],
        capture_output=True, text=True, cwd=task_dir
    )
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:300])

# Step 3: Test agent full run
print(f"\n{'='*60}")
print(f"TEST AGENT: Full run")
print(f"{'='*60}")
test_result = tester.run(
    code_result['code_file'],
    task_id,
    function_name=problem['entry_point']
)

metrics = test_result['metrics']

print(f"\n{'='*60}")
print(f"TEST AGENT RESULTS")
print(f"{'='*60}")

v = metrics.get('validity', {})
print(f"\n  1. Test Validity:")
print(f"     Valid: {v.get('valid', '?')}")
print(f"     Test functions: {v.get('test_function_count', '?')}")
print(f"     Assertions: {v.get('assert_count', '?')}")

p = metrics.get('pass_rate', {})
print(f"\n  2. Pass Rate:")
print(f"     Passed: {p.get('passed', '?')}/{p.get('total', '?')}")
print(f"     Rate: {p.get('pass_rate', '?')}")
if p.get('output'):
    print(f"     Raw output: {p['output'][:200]}")

c = metrics.get('coverage', {})
print(f"\n  3. Line Coverage:")
print(f"     Coverage: {c.get('coverage_percent', '?')}%")

s = metrics.get('smells', {})
print(f"\n  4. Test Smells: {s.get('total_smells', '?')}")

f = metrics.get('flakiness', {})
print(f"\n  5. Flakiness: {f.get('is_flaky', '?')} (runs: {f.get('runs', '?')})")
