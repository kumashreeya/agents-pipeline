"""Test improved quality agent — should no longer give false FAILs."""
from human_eval.data import read_problems
from agents.coding_agent import CodingAgent
from agents.quality_agent import QualityAgent
from tools.baseline_quality import run_baseline, compare_with_agent

problems = read_problems()
coder = CodingAgent()
quality = QualityAgent()

for task_id in ["HumanEval/0", "HumanEval/1", "HumanEval/2"]:
    problem = problems[task_id]
    code_result = coder.generate_and_save(task_id, problem["prompt"])

    # Run baseline
    baseline = run_baseline(code_result["code_file"])

    # Run improved agent
    agent_result = quality.run(code_result["code_file"])
    judgment = agent_result["judgment"]

    # Compare
    comp = compare_with_agent(baseline, agent_result)

    print(f"\n{task_id}:")
    print(f"  Baseline:  {baseline['verdict']} ({baseline['quality_score']}/100)")
    print(f"  Agent:     {judgment['verdict']} ({judgment['quality_score']}/100)")
    print(f"  Agree:     {comp['verdict_comparison']['agree']}")
    print(f"  Agreement: {comp['analysis']['agreement_rate']}%")
    print(f"  Metrics:   {judgment.get('reasoning', '')}")
    if judgment.get('failed_metrics'):
        print(f"  Failed:    {judgment['failed_metrics']}")
    if judgment.get('feedback'):
        print(f"  Feedback:  {judgment['feedback'][:100]}")
