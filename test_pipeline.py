"""
Test the pipeline: Coding Agent generates code -> Quality Agent evaluates it
This is the first connection between two agents!
"""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent


# Load problems
problems = read_problems()

# Create agents
coder = CodingAgent()
quality = QualityAgent()

# Test on one problem
task_id = "HumanEval/0"
problem = problems[task_id]

print(f"{'='*60}")
print(f"STEP 1: Coding Agent generates code")
print(f"{'='*60}")
print(f"Task: {task_id}")

# Generate code
code_result = coder.generate_and_save(task_id, problem['prompt'])

print(f"\nGenerated code:")
print(code_result['full_code'][:400])

# Check syntax
try:
    compile(code_result['full_code'], code_result['code_file'], 'exec')
    print(f"\n✓ Syntax OK")
except SyntaxError as e:
    print(f"\n✗ Syntax error: {e}")

print(f"\nSaved to: {code_result['code_file']}")


print(f"\n\n{'='*60}")
print(f"STEP 2: Quality Agent evaluates the generated code")
print(f"{'='*60}")

# Run quality agent on the generated code
quality_result = quality.run(code_result['code_file'])

# Show results
plan = quality_result['plan']
judgment = quality_result['judgment']

print(f"\n  Code purpose: {plan.get('code_purpose', '?')}")
print(f"  Risk level: {plan.get('risk_level', '?')}")
print(f"  Dangerous patterns: {plan.get('dangerous_patterns_found', [])}")

print(f"\n  Metrics checked:")
for m in plan.get('selected_metrics', []):
    print(f"    [{m.get('priority', '?')}] {m.get('metric', '?')}")

print(f"\n  {'='*50}")
print(f"  VERDICT: {judgment.get('verdict', '?')}")
print(f"  SCORE: {judgment.get('quality_score', '?')}/100")
print(f"  {'='*50}")

if judgment.get('metric_judgments'):
    for mj in judgment['metric_judgments']:
        icon = 'PASS' if mj.get('result') == 'PASS' else 'FAIL'
        print(f"  [{icon}] {mj.get('metric', '?')}: {mj.get('explanation', '?')}")

if judgment.get('feedback'):
    print(f"\n  Feedback: {judgment['feedback']}")

print(f"\n\n{'='*60}")
print(f"STEP 3: Check against HumanEval tests")
print(f"{'='*60}")

# Run the actual HumanEval tests
test_code = problem['test']
entry_point = problem['entry_point']

try:
    # Execute the generated code + tests
    exec_globals = {}
    exec(code_result['full_code'], exec_globals)
    
    # Run the check function
    check_code = test_code + f"\ncheck({entry_point})"
    exec(check_code, exec_globals)
    
    print(f"  ✓ PASSED all HumanEval tests!")
    correctness = True
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    correctness = False

print(f"\n\n{'='*60}")
print(f"COMPLETE PIPELINE SUMMARY")
print(f"{'='*60}")
print(f"  Task: {task_id}")
print(f"  Code generated: ✓")
print(f"  Syntax valid: ✓")
print(f"  Quality verdict: {judgment.get('verdict', '?')} ({judgment.get('quality_score', '?')}/100)")
print(f"  Correctness: {'PASS' if correctness else 'FAIL'}")
print(f"  Metrics checked: {[m.get('metric') for m in plan.get('selected_metrics', [])]}")
