"""Test improved test agent on 3 problems."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.test_agent import TestAgent

problems = read_problems()
coder = CodingAgent()
tester = TestAgent()

for task_id in ["HumanEval/0", "HumanEval/1", "HumanEval/2"]:
    problem = problems[task_id]
    code_result = coder.generate_and_save(task_id, problem["prompt"])

    test_result = tester.run(
        code_result["code_file"], task_id,
        function_name=problem["entry_point"]
    )

    m = test_result.get("metrics", {})
    v = m.get("validity", {})
    p = m.get("pass_rate", {})
    c = m.get("coverage", {})
    s = m.get("smells", {})

    print(f"\n{task_id}:")
    print(f"  Valid: {v.get('valid')}, Tests: {v.get('test_function_count')}, Asserts: {v.get('assert_count')}")
    print(f"  Pass rate: {p.get('passed')}/{p.get('total')} ({p.get('pass_rate')})")
    print(f"  Coverage: {c.get('coverage_percent')}%")
    print(f"  Smells: {s.get('total_smells')}")

    # Show the generated test code
    with open(test_result["test_file"], 'r') as f:
        test_code = f.read()
    print(f"  Generated tests:")
    for line in test_code.split('\n')[:15]:
        print(f"    {line}")
