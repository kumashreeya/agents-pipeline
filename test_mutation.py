"""Test mutation score on HumanEval/0."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.test_agent import TestAgent
from tools.mutation_score import measure_mutation_score

problems = read_problems()
coder = CodingAgent()
tester = TestAgent()

task_id = "HumanEval/0"
problem = problems[task_id]

# Generate code
print("Generating code...")
code_result = coder.generate_and_save(task_id, problem["prompt"])
print(f"  Code: {code_result['code_file']}")

# Generate tests
print("Generating tests...")
test_result = tester.run(code_result["code_file"], task_id, function_name=problem["entry_point"])
test_file = test_result["test_file"]
print(f"  Tests: {test_file}")
print(f"  Pass rate: {test_result['metrics']['pass_rate'].get('pass_rate', 0)}")

# Run mutation score
print()
print("Running mutation score (this may take 30-60 seconds)...")
mutation = measure_mutation_score(code_result["code_file"], test_file, timeout=120)

print()
print("=" * 60)
print("MUTATION SCORE RESULTS")
print("=" * 60)
print(f"  Score: {mutation.get('score', 0)}")
print(f"  Killed: {mutation.get('killed', 0)}")
print(f"  Survived: {mutation.get('survived', 0)}")
print(f"  Total mutants: {mutation.get('total_mutants', 0)}")
if mutation.get("error"):
    print(f"  Error: {mutation['error']}")
if mutation.get("raw_output"):
    print(f"  Raw output: {mutation['raw_output'][:300]}")
