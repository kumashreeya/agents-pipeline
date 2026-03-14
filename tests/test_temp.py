from agents.coding_agent import CodingAgent
c = CodingAgent()
prompt = 'def add(a, b):\n    """Add two numbers."""\n'
r1 = c.generate('HumanEval/0', prompt)
r2 = c.generate('HumanEval/0', prompt)
print('Run 1:', r1['full_code'].strip()[:100])
print('Run 2:', r2['full_code'].strip()[:100])
print('Same?', r1['full_code'] == r2['full_code'])
