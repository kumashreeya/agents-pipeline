"""Test the oracle validator."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.test_agent import TestAgent
from tools.test_oracle_validator import validate_test_oracle

problems = read_problems()
coder = CodingAgent()
tester = TestAgent()

for task_id in ["HumanEval/0", "HumanEval/1", "HumanEval/2"]:
    problem = problems[task_id]
    code_result = coder.generate_and_save(task_id, problem["prompt"])

    with open(code_result["code_file"], 'r') as f:
        code = f.read()

    test_result = tester.run(code_result["code_file"], task_id, function_name=problem["entry_point"])
    with open(test_result["test_file"], 'r') as f:
        test_code = f.read()

    oracle = validate_test_oracle(code, test_code, problem["entry_point"])

    print(f"\n{task_id}:")
    print(f"  Docstring examples: {oracle['docstring_examples']}")
    print(f"  Test assertions: {oracle['test_assertions']}")
    print(f"  Validated: {oracle['validated']}")
    print(f"  Mismatched: {oracle['mismatched']}")
    print(f"  Example coverage: {oracle['coverage_of_examples']}%")
    if oracle['issues']:
        print(f"  Issues: {oracle['issues'][:2]}")
