from human_eval.data import read_problems

problems = read_problems()
print(f"Total problems: {len(problems)}")
print()

# Look at the first problem
first = problems["HumanEval/0"]
print("PROBLEM ID: HumanEval/0")
print()
print("WHAT THE AI SEES (prompt):")
print(first["prompt"])
print()
print("CORRECT ANSWER:")
print(first["canonical_solution"])
print()
print("TESTS:")
print(first["test"][:300])
