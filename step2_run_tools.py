import subprocess
import json

code_file = "sample_code/bad_code.py"

# ============================================
# TOOL 1: Ruff (style/lint)
# ============================================
result = subprocess.run(
    ['ruff', 'check', code_file, '--output-format', 'json'],
    capture_output=True,
    text=True
)
ruff_issues = json.loads(result.stdout) if result.stdout else []
print(f"RUFF: Found {len(ruff_issues)} lint issues")
for issue in ruff_issues:
    print(f"  Line {issue['location']['row']}: {issue['message']}")

# ============================================
# TOOL 2: Bandit (security)
# ============================================
result = subprocess.run(
    ['bandit', '-f', 'json', '-q', code_file],
    capture_output=True,
    text=True
)
bandit_data = json.loads(result.stdout) if result.stdout else {}
findings = bandit_data.get('results', [])
high = len([f for f in findings if f['issue_severity'] == 'HIGH'])
medium = len([f for f in findings if f['issue_severity'] == 'MEDIUM'])
low = len([f for f in findings if f['issue_severity'] == 'LOW'])
print(f"\nBANDIT: Found {len(findings)} security issues (HIGH:{high}, MEDIUM:{medium}, LOW:{low})")
for f in findings:
    print(f"  [{f['issue_severity']}] {f['issue_text']} (line {f['line_number']})")

# ============================================
# TOOL 3: Radon Complexity
# ============================================
result = subprocess.run(
    ['radon', 'cc', code_file, '-j'],
    capture_output=True,
    text=True
)
radon_data = json.loads(result.stdout) if result.stdout else {}
print(f"\nRADON COMPLEXITY:")
for filename, functions in radon_data.items():
    for func in functions:
        print(f"  {func['name']}: complexity={func['complexity']} rank={func['rank']}")

# ============================================
# TOOL 4: Radon Maintainability
# ============================================
result = subprocess.run(
    ['radon', 'mi', code_file, '-j'],
    capture_output=True,
    text=True
)
mi_data = json.loads(result.stdout) if result.stdout else {}
print(f"\nRADON MAINTAINABILITY:")
for filename, score in mi_data.items():
    print(f"  {filename}: score={score}")

# ============================================
# TOOL 5: Mypy (type errors)
# ============================================
result = subprocess.run(
    ['mypy', '--strict', '--no-error-summary', code_file],
    capture_output=True,
    text=True
)
errors = [line for line in result.stdout.split('\n') if 'error:' in line]
print(f"\nMYPY: Found {len(errors)} type errors")
for e in errors:
    print(f"  {e}")

# ============================================
# SUMMARY
# ============================================
print(f"\n{'='*50}")
print(f"SUMMARY FOR: {code_file}")
print(f"{'='*50}")
print(f"  Lint issues:      {len(ruff_issues)}")
print(f"  Security issues:  {len(findings)} (HIGH:{high}, MED:{medium}, LOW:{low})")
print(f"  Type errors:      {len(errors)}")
print(f"  Complexity:       {radon_data.get(code_file, [{}])[0].get('complexity', 'N/A') if radon_data.get(code_file) else 'N/A'}")
print(f"  Maintainability:  {mi_data.get(code_file, 'N/A')}")
