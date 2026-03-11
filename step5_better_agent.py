import subprocess
import json
from ollama import chat


# ============================================
# TOOL FUNCTIONS (same as before)
# ============================================

def measure_lint(code_file):
    result = subprocess.run(['ruff', 'check', code_file, '--output-format', 'json'], capture_output=True, text=True)
    issues = json.loads(result.stdout) if result.stdout else []
    return {'total': len(issues), 'details': [{'line': i['location']['row'], 'message': i['message']} for i in issues[:5]]}

def measure_security(code_file):
    result = subprocess.run(['bandit', '-f', 'json', '-q', code_file], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    findings = data.get('results', [])
    return {
        'high': len([f for f in findings if f['issue_severity'] == 'HIGH']),
        'medium': len([f for f in findings if f['issue_severity'] == 'MEDIUM']),
        'low': len([f for f in findings if f['issue_severity'] == 'LOW']),
        'total': len(findings),
        'details': [{'severity': f['issue_severity'], 'description': f['issue_text'], 'line': f['line_number']} for f in findings]
    }

def measure_complexity(code_file):
    result = subprocess.run(['radon', 'cc', code_file, '-j'], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    functions = []
    for filename, items in data.items():
        for item in items:
            functions.append({'name': item['name'], 'complexity': item['complexity'], 'rank': item['rank']})
    avg = sum(f['complexity'] for f in functions) / len(functions) if functions else 0
    return {'functions': functions, 'average': round(avg, 2), 'max': max((f['complexity'] for f in functions), default=0)}

def measure_maintainability(code_file):
    result = subprocess.run(['radon', 'mi', code_file, '-j'], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, score in data.items():
        if isinstance(score, dict):
            return {'score': round(score.get('mi', 0), 2), 'rank': score.get('rank', '?')}
        return {'score': round(score, 2) if isinstance(score, (int, float)) else 0, 'rank': '?'}
    return {'score': 0, 'rank': '?'}

def measure_types(code_file):
    result = subprocess.run(['mypy', '--strict', '--no-error-summary', code_file], capture_output=True, text=True)
    errors = [line for line in result.stdout.split('\n') if 'error:' in line]
    return {'total_errors': len(errors), 'details': errors[:5]}

def measure_halstead(code_file):
    result = subprocess.run(['radon', 'hal', code_file, '-j'], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, metrics in data.items():
        total = metrics.get('total', [{}])
        if isinstance(total, list) and len(total) > 0:
            t = total[0]
        elif isinstance(total, dict):
            t = total
        else:
            t = {}
        return {'difficulty': round(t.get('difficulty', 0), 2), 'effort': round(t.get('effort', 0), 2), 'volume': round(t.get('volume', 0), 2), 'bugs': round(t.get('bugs', 0), 4)}
    return {'difficulty': 0, 'effort': 0, 'volume': 0, 'bugs': 0}

def measure_sloc(code_file):
    result = subprocess.run(['radon', 'raw', code_file, '-j'], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, metrics in data.items():
        return {'loc': metrics.get('loc', 0), 'sloc': metrics.get('sloc', 0), 'comments': metrics.get('comments', 0), 'blank': metrics.get('blank', 0)}
    return {'loc': 0, 'sloc': 0, 'comments': 0, 'blank': 0}


METRIC_FUNCTIONS = {
    'lint_violations': measure_lint,
    'security_vulnerabilities': measure_security,
    'cyclomatic_complexity': measure_complexity,
    'maintainability_index': measure_maintainability,
    'type_errors': measure_types,
    'halstead_difficulty': measure_halstead,
    'sloc': measure_sloc,
}


# ============================================
# IMPROVED AGENT with better prompting
# ============================================

def run_quality_agent(code_file):
    with open(code_file, 'r') as f:
        code = f.read()

    print(f"\n{'='*60}")
    print(f"QUALITY AGENT - Analyzing: {code_file}")
    print(f"{'='*60}")

    # ==========================================
    # PHASE 1: PLAN - improved prompt
    # ==========================================
    print(f"\n--- PHASE 1: Planning ---")

    plan_response = chat(
        model='qwen2.5-coder:3b',
        messages=[
            {
                'role': 'system',
                'content': """You are a senior code quality expert. Your job is to decide which quality metrics to measure for a given piece of code.

AVAILABLE METRICS:
1. lint_violations — style and best practice issues (ruff)
2. security_vulnerabilities — CWE vulnerability patterns: injection, unsafe deserialization, command execution (bandit). IMPORTANT: select this if the code uses ANY of these: eval, exec, pickle, os.system, subprocess, open(), socket, SQL strings, user input
3. cyclomatic_complexity — number of paths through code, 1-5=simple, 6-10=moderate, 11+=complex (radon)
4. maintainability_index — combined quality score 0-100, above 40=good (radon)
5. type_errors — type annotation errors under strict checking (mypy)
6. halstead_difficulty — how error-prone the code is (radon)
7. sloc — lines of code counts (radon)

RULES:
- You MUST select security_vulnerabilities if the code contains eval, exec, pickle, os.system, subprocess, open(), or string-concatenated SQL
- Select at least 3 metrics for any code
- Select at least 5 metrics for medium or high risk code"""
            },
            {
                'role': 'user',
                'content': f"""Analyze this code and decide which metrics to measure.
```python
{code}
```

FIRST, list every potentially dangerous function or pattern you see in the code.
THEN, select your metrics.

Respond with ONLY JSON:
{{
    "code_purpose": "one sentence",
    "dangerous_patterns_found": ["list every risky function/pattern you see"],
    "risk_level": "low or medium or high",
    "selected_metrics": [
        {{
            "metric": "exact name from list",
            "why": "one sentence",
            "threshold": "acceptable value",
            "priority": "critical or important or informational"
        }}
    ],
    "skipped_metrics": [
        {{"metric": "name", "why_skipped": "one sentence"}}
    ]
}}"""
            }
        ]
    )

    plan_text = plan_response.message.content.strip()
    if plan_text.startswith('```'):
        plan_text = plan_text.split('\n', 1)[1]
    if '```' in plan_text:
        plan_text = plan_text.split('```')[0]

    try:
        plan = json.loads(plan_text)
    except json.JSONDecodeError:
        print(f"  Could not parse plan. Using all metrics as fallback.")
        plan = {
            'code_purpose': 'unknown',
            'dangerous_patterns_found': [],
            'risk_level': 'medium',
            'selected_metrics': [{'metric': name, 'why': 'fallback', 'threshold': 'N/A', 'priority': 'important'} for name in METRIC_FUNCTIONS.keys()],
            'skipped_metrics': []
        }

    print(f"  Purpose: {plan.get('code_purpose', '?')}")
    print(f"  Dangerous patterns: {plan.get('dangerous_patterns_found', [])}")
    print(f"  Risk: {plan.get('risk_level', '?')}")
    print(f"  Selected metrics:")
    for m in plan.get('selected_metrics', []):
        print(f"    [{m.get('priority', '?')}] {m.get('metric', '?')}")
        print(f"      Why: {m.get('why', '?')}")
        print(f"      Threshold: {m.get('threshold', '?')}")
    if plan.get('skipped_metrics'):
        print(f"  Skipped:")
        for s in plan['skipped_metrics']:
            print(f"    {s.get('metric', '?')}: {s.get('why_skipped', '?')}")

    # ==========================================
    # PHASE 2: MEASURE
    # ==========================================
    print(f"\n--- PHASE 2: Measuring ---")

    measurements = {}
    for metric_info in plan.get('selected_metrics', []):
        metric_name = metric_info.get('metric', '')
        if metric_name in METRIC_FUNCTIONS:
            print(f"  Measuring: {metric_name}...")
            measurements[metric_name] = METRIC_FUNCTIONS[metric_name](code_file)
        else:
            print(f"  Unknown metric: {metric_name}")

    for name, result in measurements.items():
        print(f"  Result — {name}: {json.dumps(result, default=str)[:100]}")

    # ==========================================
    # PHASE 3: JUDGE
    # ==========================================
    print(f"\n--- PHASE 3: Judging ---")

    judge_response = chat(
        model='qwen2.5-coder:3b',
        messages=[
            {
                'role': 'system',
                'content': 'You are a strict code quality judge. Compare measurements against thresholds and give honest verdicts.'
            },
            {
                'role': 'user',
                'content': f"""Judge this code quality.

CODE:
```python
{code}
```

PLAN: {json.dumps(plan, indent=2)}

MEASUREMENTS: {json.dumps(measurements, indent=2, default=str)}

Compare each measurement against the threshold from the plan.
If ANY critical metric fails, the overall verdict must be FAIL.

Respond with ONLY JSON:
{{
    "verdict": "PASS or FAIL or NEEDS_IMPROVEMENT",
    "quality_score": "0 to 100",
    "reasoning": "one sentence",
    "metric_judgments": [
        {{"metric": "name", "threshold": "what you set", "measured": "what was found", "result": "PASS or FAIL", "explanation": "one sentence"}}
    ],
    "top_issues": ["most important issue first", "second issue", "third issue"],
    "feedback": "specific instructions for fixing the code"
}}"""
            }
        ]
    )

    judge_text = judge_response.message.content.strip()
    if judge_text.startswith('```'):
        judge_text = judge_text.split('\n', 1)[1]
    if '```' in judge_text:
        judge_text = judge_text.split('```')[0]

    try:
        judgment = json.loads(judge_text)
    except json.JSONDecodeError:
        judgment = {'verdict': 'UNKNOWN', 'raw': judge_text[:500]}

    print(f"\n{'='*60}")
    print(f"VERDICT: {judgment.get('verdict', '?')}")
    print(f"SCORE: {judgment.get('quality_score', '?')}/100")
    print(f"REASON: {judgment.get('reasoning', '?')}")
    print(f"{'='*60}")

    if judgment.get('metric_judgments'):
        for mj in judgment['metric_judgments']:
            icon = 'PASS' if mj.get('result') == 'PASS' else 'FAIL'
            print(f"  [{icon}] {mj.get('metric', '?')}: {mj.get('explanation', '?')}")

    if judgment.get('top_issues'):
        print(f"\nFix these:")
        for i, issue in enumerate(judgment['top_issues'], 1):
            print(f"  {i}. {issue}")

    if judgment.get('feedback'):
        print(f"\nFeedback: {judgment['feedback']}")

    log_data = {'code_file': code_file, 'plan': plan, 'measurements': measurements, 'judgment': judgment}
    log_file = f"logs/{code_file.replace('/', '_')}_quality_log.json"
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2, default=str)
    print(f"\nLog saved: {log_file}")

    return log_data


if __name__ == '__main__':
    print("\nTEST 1: Good code")
    run_quality_agent('sample_code/good_code.py')

    print("\n\nTEST 2: Bad code")
    run_quality_agent('sample_code/bad_code.py')
