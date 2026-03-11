"""
Autonomous Quality Agent
Decides which metrics to check, runs them, and judges results.
"""
import json
import datetime
from ollama import chat
from tools.metric_runners import ALL_METRICS, run_metric


METRIC_CATALOG = """
AVAILABLE METRICS:
1. lint_violations — style and best practice issues (ruff)
2. security_vulnerabilities — CWE vulnerability patterns: injection, unsafe deserialization, command execution (bandit). MUST select if code uses eval, exec, pickle, os.system, subprocess, open(), socket, or SQL strings
3. cyclomatic_complexity — paths through code. 1-5=simple, 6-10=moderate, 11+=complex (radon)
4. maintainability_index — combined score 0-100. Above 40=good, 20-40=moderate, below 20=poor (radon)
5. type_errors — type annotation errors under strict checking (mypy)
6. halstead_difficulty — how error-prone the code is. Higher=worse (radon)
7. sloc — source lines of code, comment lines, blank lines (radon)
"""


class QualityAgent:
    """An autonomous agent that evaluates code quality."""

    def __init__(self, model='qwen2.5-coder:3b'):
        self.model = model

    def plan(self, code):
        """Phase 1: Agent reads code and decides what to check."""
        response = chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': f"""You are a senior code quality expert. Decide which quality metrics to measure.
{METRIC_CATALOG}
RULES:
- MUST select security_vulnerabilities if code contains eval, exec, pickle, os.system, subprocess, open(), or SQL strings
- Select at least 3 metrics for any code
- Select at least 5 metrics for medium or high risk code"""
                },
                {
                    'role': 'user',
                    'content': f"""Analyze this code and decide which metrics to measure.
```python
{code}
```

FIRST list every dangerous function or pattern you see.
THEN select your metrics.

Respond with ONLY JSON:
{{
    "code_purpose": "one sentence",
    "dangerous_patterns_found": ["list every risky pattern"],
    "risk_level": "low or medium or high",
    "selected_metrics": [
        {{"metric": "exact name from list", "why": "one sentence", "threshold": "acceptable value", "priority": "critical or important or informational"}}
    ],
    "skipped_metrics": [
        {{"metric": "name", "why_skipped": "one sentence"}}
    ]
}}"""
                }
            ]
        )

        text = response.message.content.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
        if '```' in text:
            text = text.split('```')[0]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {
                'code_purpose': 'unknown',
                'dangerous_patterns_found': [],
                'risk_level': 'medium',
                'selected_metrics': [{'metric': name, 'why': 'fallback', 'threshold': 'N/A', 'priority': 'important'} for name in ALL_METRICS.keys()],
                'skipped_metrics': []
            }

    def measure(self, code_file, plan):
        """Phase 2: Run selected metrics."""
        measurements = {}
        for metric_info in plan.get('selected_metrics', []):
            metric_name = metric_info.get('metric', '')
            if metric_name in ALL_METRICS:
                measurements[metric_name] = run_metric(metric_name, code_file)
        return measurements

    def judge(self, code, plan, measurements):
        """Phase 3: Agent judges results against its own thresholds."""
        response = chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a strict code quality judge. If ANY critical metric fails, overall verdict must be FAIL.'
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

Respond with ONLY JSON:
{{
    "verdict": "PASS or FAIL or NEEDS_IMPROVEMENT",
    "quality_score": "0 to 100",
    "reasoning": "one sentence",
    "metric_judgments": [
        {{"metric": "name", "threshold": "what you set", "measured": "what was found", "result": "PASS or FAIL", "explanation": "one sentence"}}
    ],
    "top_issues": ["issue 1", "issue 2", "issue 3"],
    "feedback": "specific fix instructions for coding agent"
}}"""
                }
            ]
        )

        text = response.message.content.strip()
        if text.startswith('```'):
            text = text.split('\n', 1)[1]
        if '```' in text:
            text = text.split('```')[0]

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {'verdict': 'UNKNOWN', 'raw': text[:500]}

    def run(self, code_file):
        """Run the full quality agent pipeline: plan -> measure -> judge."""
        with open(code_file, 'r') as f:
            code = f.read()

        # Phase 1
        plan = self.plan(code)

        # Phase 2
        measurements = self.measure(code_file, plan)

        # Phase 3
        judgment = self.judge(code, plan, measurements)

        # Save log
        log_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'code_file': code_file,
            'model': self.model,
            'plan': plan,
            'measurements': measurements,
            'judgment': judgment
        }

        log_file = f"logs/{code_file.replace('/', '_')}_log.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)

        return log_data
