import subprocess
import json
from ollama import chat


# ============================================
# TOOL FUNCTIONS - The agent's "hands"
# ============================================

def measure_lint(code_file):
    result = subprocess.run(
        ['ruff', 'check', code_file, '--output-format', 'json'],
        capture_output=True, text=True
    )
    issues = json.loads(result.stdout) if result.stdout else []
    return {'total': len(issues), 'details': [{'line': i['location']['row'], 'message': i['message']} for i in issues[:5]]}


def measure_security(code_file):
    result = subprocess.run(
        ['bandit', '-f', 'json', '-q', code_file],
        capture_output=True, text=True
    )
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
    result = subprocess.run(
        ['radon', 'cc', code_file, '-j'],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout) if result.stdout else {}
    functions = []
    for filename, items in data.items():
        for item in items:
            functions.append({'name': item['name'], 'complexity': item['complexity'], 'rank': item['rank']})
    avg = sum(f['complexity'] for f in functions) / len(functions) if functions else 0
    return {'functions': functions, 'average': round(avg, 2), 'max': max((f['complexity'] for f in functions), default=0)}


def measure_maintainability(code_file):
    result = subprocess.run(
        ['radon', 'mi', code_file, '-j'],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, score in data.items():
        if isinstance(score, dict):
            return {'score': round(score.get('mi', 0), 2), 'rank': score.get('rank', '?')}
        return {'score': round(score, 2) if isinstance(score, (int, float)) else 0, 'rank': '?'}
    return {'score': 0, 'rank': '?'}


def measure_types(code_file):
    result = subprocess.run(
        ['mypy', '--strict', '--no-error-summary', code_file],
        capture_output=True, text=True
    )
    errors = [line for line in result.stdout.split('\n') if 'error:' in line]
    return {'total_errors': len(errors), 'details': errors[:5]}


def measure_halstead(code_file):
    result = subprocess.run(
        ['radon', 'hal', code_file, '-j'],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, metrics in data.items():
        total = metrics.get('total', [{}])
        if isinstance(total, list) and len(total) > 0:
            t = total[0]
        elif isinstance(total, dict):
            t = total
        else:
            t = {}
        return {
            'difficulty': round(t.get('difficulty', 0), 2),
            'effort': round(t.get('effort', 0), 2),
            'volume': round(t.get('volume', 0), 2),
            'bugs': round(t.get('bugs', 0), 4)
        }
    return {'difficulty': 0, 'effort': 0, 'volume': 0, 'bugs': 0}


def measure_sloc(code_file):
    result = subprocess.run(
        ['radon', 'raw', code_file, '-j'],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, metrics in data.items():
        return {
            'loc': metrics.get('loc', 0),
            'sloc': metrics.get('sloc', 0),
            'comments': metrics.get('comments', 0),
            'blank': metrics.get('blank', 0)
        }
    return {'loc': 0, 'sloc': 0, 'comments': 0, 'blank': 0}


# Map of metric names to functions
METRIC_FUNCTIONS = {
    'lint_violations': measure_lint,
    'security_vulnerabilities': measure_security,
    'cyclomatic_complexity': measure_complexity,
    'maintainability_index': measure_maintainability,
    'type_errors': measure_types,
    'halstead_difficulty': measure_halstead,
    'sloc': measure_sloc,
}

METRIC_CATALOG = """
AVAILABLE QUALITY METRICS:
1. lint_violations — PEP8 and Python best practice violations (tool: ruff)
2. security_vulnerabilities — CWE-based vulnerability patterns by severity HIGH/MEDIUM/LOW (tool: bandit)
3. cyclomatic_complexity — McCabe complexity, counts paths through code. 1-5=simple, 6-10=moderate, 11+=complex (tool: radon)
4. maintainability_index — Combined score 0-100. Above 40=good, 20-40=moderate, below 20=poor (tool: radon)
5. type_errors — Static type checking errors under strict mode (tool: mypy)
6. halstead_difficulty — How error-prone the code is. Higher=worse (tool: radon)
7. sloc — Source lines of code, comment lines, blank lines (tool: radon)
"""


# ============================================
# THE AGENT - Decides what to check and judges results
# ============================================

def run_quality_agent(code_file):
    """The autonomous quality agent."""

    # Read the code
    with open(code_file, 'r') as f:
        code = f.read()

    print(f"\n{'='*60}")
    print(f"QUALITY AGENT - Analyzing: {code_file}")
    print(f"{'='*60}")

    # ==========================================
    # PHASE 1: Agent PLANS what to check
    # ==========================================
    print(f"\n--- PHASE 1: Agent deciding what to check ---")

    plan_response = chat(
        model='qwen2.5-coder:3b',
        messages=[
            {
                'role': 'system',
                'content': f"""You are a code quality expert. You decide which metrics to measure for each piece of code.
{METRIC_CATALOG}
You do NOT have to use all metrics. Choose only what is relevant for THIS specific code."""
            },
            {
                'role': 'user',
                'content': f"""Analyze this code and decide which quality metrics to measure.
```python
{code}
```

Respond with ONLY a JSON object, no other text:
{{
    "code_purpose": "what this code does in one sentence",
    "risk_level": "low or medium or high",
    "selected_metrics": [
        {{
            "metric": "exact metric name from the list",
            "why": "one sentence why this matters for this code",
            "threshold": "what value is acceptable",
            "priority": "critical or important or informational"
        }}
    ],
    "skipped_metrics": [
        {{
            "metric": "metric name",
            "why_skipped": "one sentence why not relevant"
        }}
    ]
}}"""
            }
        ]
    )

    # Parse the plan
    plan_text = plan_response.message.content.strip()
    if plan_text.startswith('```'):
        plan_text = plan_text.split('\n', 1)[1]
    if '```' in plan_text:
        plan_text = plan_text.split('```')[0]

    try:
        plan = json.loads(plan_text)
    except json.JSONDecodeError:
        print(f"  Warning: Could not parse agent's plan. Using all metrics.")
        plan = {
            'code_purpose': 'unknown',
            'risk_level': 'medium',
            'selected_metrics': [{'metric': name, 'why': 'fallback', 'threshold': 'N/A', 'priority': 'important'} for name in METRIC_FUNCTIONS.keys()],
            'skipped_metrics': []
        }

    # Show the plan
    print(f"  Purpose: {plan.get('code_purpose', '?')}")
    print(f"  Risk: {plan.get('risk_level', '?')}")
    print(f"  Metrics selected:")
    for m in plan.get('selected_metrics', []):
        print(f"    [{m.get('priority', '?')}] {m.get('metric', '?')} — {m.get('why', '?')}")
        print(f"      Threshold: {m.get('threshold', '?')}")
    if plan.get('skipped_metrics'):
        print(f"  Metrics SKIPPED:")
        for s in plan['skipped_metrics']:
            print(f"    {s.get('metric', '?')} — {s.get('why_skipped', '?')}")

    # ==========================================
    # PHASE 2: Agent MEASURES selected metrics
    # ==========================================
    print(f"\n--- PHASE 2: Running measurements ---")

    measurements = {}
    for metric_info in plan.get('selected_metrics', []):
        metric_name = metric_info.get('metric', '')
        if metric_name in METRIC_FUNCTIONS:
            print(f"  Measuring: {metric_name}...")
            measurements[metric_name] = METRIC_FUNCTIONS[metric_name](code_file)
        else:
            print(f"  Skipping unknown metric: {metric_name}")

    # Show raw measurements
    for name, result in measurements.items():
        print(f"  {name}: {json.dumps(result, default=str)[:120]}")

    # ==========================================
    # PHASE 3: Agent JUDGES the results
    # ==========================================
    print(f"\n--- PHASE 3: Agent judging results ---")

    judge_response = chat(
        model='qwen2.5-coder:3b',
        messages=[
            {
                'role': 'system',
                'content': 'You are a code quality expert making a final judgment.'
            },
            {
                'role': 'user',
                'content': f"""You planned to check this code:
```python
{code}
```

Your plan was:
{json.dumps(plan, indent=2)}

The measurements are:
{json.dumps(measurements, indent=2, default=str)}

Judge each metric against YOUR threshold. Respond with ONLY JSON:
{{
    "verdict": "PASS or FAIL or NEEDS_IMPROVEMENT",
    "quality_score": "0 to 100",
    "reasoning": "one sentence explanation",
    "metric_judgments": [
        {{
            "metric": "name",
            "threshold": "what you set",
            "measured": "what was found",
            "result": "PASS or FAIL or WARNING",
            "explanation": "one sentence"
        }}
    ],
    "top_issues": ["issue 1 to fix", "issue 2 to fix", "issue 3 to fix"],
    "feedback": "what to tell the coding agent to fix"
}}"""
            }
        ]
    )

    # Parse judgment
    judge_text = judge_response.message.content.strip()
    if judge_text.startswith('```'):
        judge_text = judge_text.split('\n', 1)[1]
    if '```' in judge_text:
        judge_text = judge_text.split('```')[0]

    try:
        judgment = json.loads(judge_text)
    except json.JSONDecodeError:
        print(f"  Warning: Could not parse judgment. Raw response:")
        print(f"  {judge_text[:500]}")
        judgment = {'verdict': 'UNKNOWN', 'raw': judge_text}

    # Show the verdict
    print(f"\n{'='*60}")
    print(f"VERDICT: {judgment.get('verdict', '?')}")
    print(f"QUALITY SCORE: {judgment.get('quality_score', '?')}/100")
    print(f"REASONING: {judgment.get('reasoning', '?')}")
    print(f"{'='*60}")

    if judgment.get('metric_judgments'):
        print(f"\nMetric-by-metric:")
        for mj in judgment['metric_judgments']:
            icon = 'PASS' if mj.get('result') == 'PASS' else 'FAIL' if mj.get('result') == 'FAIL' else 'WARN'
            print(f"  [{icon}] {mj.get('metric', '?')}: {mj.get('explanation', '?')}")

    if judgment.get('top_issues'):
        print(f"\nTop issues to fix:")
        for i, issue in enumerate(judgment['top_issues'], 1):
            print(f"  {i}. {issue}")

    if judgment.get('feedback'):
        print(f"\nFeedback for coding agent:")
        print(f"  {judgment['feedback']}")

    # Save results to a log file
    log_data = {
        'code_file': code_file,
        'plan': plan,
        'measurements': measurements,
        'judgment': judgment
    }
    log_file = f"logs/{code_file.replace('/', '_')}_quality_log.json"
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2, default=str)
    print(f"\nLog saved to: {log_file}")

    return log_data


# ============================================
# RUN IT
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("TEST 1: Clean code")
    print("="*60)
    result1 = run_quality_agent('sample_code/good_code.py')

    print("\n\n" + "="*60)
    print("TEST 2: Risky code")
    print("="*60)
    result2 = run_quality_agent('sample_code/bad_code.py')
