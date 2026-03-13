"""Test AI-specific metrics on generated code."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from tools.ai_specific_metrics import run_all_ai_metrics

problems = read_problems()
coder = CodingAgent()

task_ids = ["HumanEval/0", "HumanEval/1", "HumanEval/2"]

for task_id in task_ids:
    problem = problems[task_id]
    code_result = coder.generate_and_save(task_id, problem["prompt"])

    print()
    print("=" * 60)
    print("AI-SPECIFIC METRICS:", task_id)
    print("=" * 60)

    ai_metrics = run_all_ai_metrics(code_result["code_file"])

    # Dead code
    dc = ai_metrics["dead_code"]
    print(f"  Dead Code: {dc['total']} issues")
    if dc.get("details"):
        for d in dc["details"][:3]:
            print(f"    - {d}")

    # Hallucinated imports
    hi = ai_metrics["hallucinated_imports"]
    print(f"  Hallucinated Imports: {hi['total']}")
    if hi.get("hallucinated"):
        print(f"    Fake: {hi['hallucinated']}")
    print(f"    Valid: {hi.get('valid', [])}")

    # Code duplication
    cd = ai_metrics["code_duplication"]
    print(f"  Code Duplication: {cd['total']} issues")
    print(f"    Duplicate functions: {cd['duplicate_functions']}")
    if cd.get("duplicate_function_details"):
        for d in cd["duplicate_function_details"]:
            print(f"    - {d['function']} defined {d['count']+1} times")
    print(f"    Repeated blocks: {cd['repeated_blocks']}")
    print(f"    All functions: {cd['all_functions']}")

# Also test on bad code
print()
print("=" * 60)
print("AI-SPECIFIC METRICS: sample_code/bad_code.py")
print("=" * 60)
ai_bad = run_all_ai_metrics("sample_code/bad_code.py")
dc = ai_bad["dead_code"]
print(f"  Dead Code: {dc['total']} issues")
if dc.get("details"):
    for d in dc["details"][:3]:
        print(f"    - {d}")
hi = ai_bad["hallucinated_imports"]
print(f"  Hallucinated Imports: {hi['total']}")
cd = ai_bad["code_duplication"]
print(f"  Code Duplication: {cd['total']} issues")
