"""Test fixed coding agent - check for duplicates."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from tools.ai_specific_metrics import measure_code_duplication

problems = read_problems()
coder = CodingAgent()

for task_id in ["HumanEval/0", "HumanEval/1", "HumanEval/2"]:
    problem = problems[task_id]
    result = coder.generate_and_save(task_id, problem["prompt"])

    dup = measure_code_duplication(result["code_file"])

    print()
    print(task_id + ":")
    print("  Valid:", result.get("valid", "?"))
    print("  Issue:", result.get("validation_issue", "?"))
    print("  Duplicates:", dup["duplicate_functions"])
    print("  Functions:", dup["all_functions"])
    print("  Code preview:")
    preview = result["full_code"][:300]
    print(preview)
