from human_eval.data import read_problems
from agents.coding_agent import CodingAgent

# Load problems
problems = read_problems()

# Create coding agent
agent = CodingAgent()

# Test on first 3 problems
test_ids = ["HumanEval/0", "HumanEval/1", "HumanEval/2"]

for task_id in test_ids:
    problem = problems[task_id]
    
    print(f"\n{'='*60}")
    print(f"TASK: {task_id}")
    print(f"{'='*60}")
    
    print(f"\nProblem (first 200 chars):")
    print(problem['prompt'][:200])
    
    # Generate code
    print(f"\nGenerating code...")
    result = agent.generate_and_save(task_id, problem['prompt'])
    
    print(f"\nGenerated code:")
    print(result['full_code'][:500])
    
    print(f"\nSaved to: {result['code_file']}")
    
    # Quick check: does it even run without errors?
    print(f"\nSyntax check...")
    try:
        compile(result['full_code'], result['code_file'], 'exec')
        print(f"  ✓ Code compiles successfully")
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
