import subprocess
import json
from ollama import chat

code_file = "sample_code/bad_code.py"

# Read the code
with open(code_file, 'r') as f:
    code = f.read()

# ============================================
# Run all tools and collect results
# ============================================
print("Running quality tools...")

# Ruff
result = subprocess.run(['ruff', 'check', code_file, '--output-format', 'json'], capture_output=True, text=True)
ruff_issues = json.loads(result.stdout) if result.stdout else []

# Bandit
result = subprocess.run(['bandit', '-f', 'json', '-q', code_file], capture_output=True, text=True)
bandit_data = json.loads(result.stdout) if result.stdout else {}
findings = bandit_data.get('results', [])

# Radon
result = subprocess.run(['radon', 'cc', code_file, '-j'], capture_output=True, text=True)
complexity_data = json.loads(result.stdout) if result.stdout else {}

result = subprocess.run(['radon', 'mi', code_file, '-j'], capture_output=True, text=True)
mi_data = json.loads(result.stdout) if result.stdout else {}

# Mypy
result = subprocess.run(['mypy', '--strict', '--no-error-summary', code_file], capture_output=True, text=True)
type_errors = [line for line in result.stdout.split('\n') if 'error:' in line]

print("Tools finished. Asking AI to analyze...\n")

# ============================================
# Build a summary for the AI
# ============================================
tool_summary = f"""
RUFF (lint): {len(ruff_issues)} issues
BANDIT (security): {len(findings)} issues
"""
for f in findings:
    tool_summary += f"  - [{f['issue_severity']}] {f['issue_text']} (line {f['line_number']})\n"

tool_summary += f"""
RADON COMPLEXITY: {complexity_data.get(code_file, [{}])[0].get('complexity', 'N/A') if complexity_data.get(code_file) else 'N/A'}
RADON MAINTAINABILITY: {mi_data.get(code_file, 'N/A')}
MYPY (types): {len(type_errors)} type errors
"""

# ============================================
# Ask the AI to interpret everything
# ============================================
response = chat(
    model='qwen2.5-coder:3b',
    messages=[
        {
            'role': 'system',
            'content': 'You are a code quality expert. Analyze tool results and give specific, actionable feedback.'
        },
        {
            'role': 'user',
            'content': f"""Here is a Python function and the results from quality analysis tools.

CODE:
```python
{code}
```

TOOL RESULTS:
{tool_summary}

Based on these results:
1. What is the most critical issue to fix FIRST?
2. Give the specific code fix for the top 3 issues
3. Rate the overall quality: PASS / FAIL / NEEDS IMPROVEMENT

Be brief and specific."""
        }
    ]
)

print("AI QUALITY ANALYSIS:")
print("=" * 50)
print(response.message.content)
