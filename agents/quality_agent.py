"""
Autonomous Quality Agent
Phase 1 (PLAN): LLM decides what to check
Phase 2 (MEASURE): Tools run deterministically
Phase 3 (JUDGE): Code compares numbers + LLM provides feedback
"""
import json
import datetime
from ollama import chat
from tools.metric_runners import ALL_METRICS, run_metric


METRIC_CATALOG = """
AVAILABLE METRICS:
1. lint_violations — style and best practice issues (ruff)
2. security_vulnerabilities — CWE vulnerability patterns (bandit). MUST select if code uses eval, exec, pickle, os.system, subprocess, open(), socket, or SQL strings
3. cyclomatic_complexity — paths through code. 1-5=simple, 6-10=moderate, 11+=complex (radon)
4. maintainability_index — combined score 0-100. Above 40=good, 20-40=moderate, below 20=poor (radon)
5. type_errors — type annotation errors under strict checking (mypy)
6. halstead_difficulty — how error-prone the code is. Higher=worse (radon)
7. sloc — source lines of code, comment lines, blank lines (radon)
"""

# Fixed thresholds for deterministic judging — LLM no longer does math
DEFAULT_THRESHOLDS = {
    'lint_violations': {'field': 'total', 'op': '<=', 'value': 5, 'desc': 'Max 5 lint violations'},
    'security_vulnerabilities': {'field': 'high', 'op': '==', 'value': 0, 'desc': 'Zero HIGH severity vulnerabilities'},
    'cyclomatic_complexity': {'field': 'average', 'op': '<=', 'value': 10, 'desc': 'Average complexity <= 10'},
    'maintainability_index': {'field': 'score', 'op': '>=', 'value': 20, 'desc': 'MI score >= 20'},
    'type_errors': {'field': 'total_errors', 'op': '<=', 'value': 5, 'desc': 'Max 5 type errors'},
    'halstead_difficulty': {'field': 'difficulty', 'op': '<=', 'value': 30, 'desc': 'Difficulty <= 30'},
    'sloc': {'field': 'sloc', 'op': '<=', 'value': 200, 'desc': 'Source lines <= 200'},
}


class QualityAgent:
    """An autonomous agent that evaluates code quality."""

    def __init__(self, model='qwen2.5-coder:3b'):
        self.model = model

    def plan(self, code):
        """Phase 1: LLM reads code and decides what to check."""
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
        {{"metric": "exact name from list", "why": "one sentence", "priority": "critical or important or informational"}}
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
                'selected_metrics': [{'metric': name, 'why': 'fallback', 'priority': 'important'} for name in ALL_METRICS.keys()],
                'skipped_metrics': []
            }

    def measure(self, code_file, plan):
        """Phase 2: Run selected metrics deterministically."""
        measurements = {}
        for metric_info in plan.get('selected_metrics', []):
            metric_name = metric_info.get('metric', '')
            if metric_name in ALL_METRICS:
                measurements[metric_name] = run_metric(metric_name, code_file)
        return measurements

    def _compare(self, value, op, threshold):
        """Deterministic comparison — no LLM needed."""
        if op == '<=': return value <= threshold
        if op == '>=': return value >= threshold
        if op == '==': return value == threshold
        if op == '<':  return value < threshold
        if op == '>':  return value > threshold
        return True

    def judge(self, code, plan, measurements):
        """Phase 3: Code does math, LLM provides feedback only."""

        # Step 1: DETERMINISTIC comparison (Python, not LLM)
        metric_judgments = []
        failed_metrics = []
        passed_metrics = []

        for metric_info in plan.get('selected_metrics', []):
            metric_name = metric_info.get('metric', '')
            if metric_name not in measurements:
                continue

            measurement = measurements[metric_name]
            threshold_info = DEFAULT_THRESHOLDS.get(metric_name)

            if threshold_info:
                field = threshold_info['field']
                value = measurement.get(field, 0)
                op = threshold_info['op']
                thresh = threshold_info['value']
                passed = self._compare(value, op, thresh)

                judgment = {
                    'metric': metric_name,
                    'measured_value': value,
                    'threshold': thresh,
                    'comparison': op,
                    'result': 'PASS' if passed else 'FAIL',
                    'priority': metric_info.get('priority', 'important'),
                    'description': threshold_info['desc'],
                }
                metric_judgments.append(judgment)

                if passed:
                    passed_metrics.append(metric_name)
                else:
                    failed_metrics.append(metric_name)

        # Step 2: DETERMINISTIC verdict
        critical_fails = [j for j in metric_judgments 
                         if j['result'] == 'FAIL' and j['priority'] == 'critical']
        
        if critical_fails:
            verdict = 'FAIL'
        elif len(failed_metrics) >= 3:
            verdict = 'FAIL'
        elif len(failed_metrics) >= 1:
            verdict = 'NEEDS_IMPROVEMENT'
        else:
            verdict = 'PASS'

        # Step 3: Calculate quality score (deterministic)
        total = len(metric_judgments)
        passed_count = len(passed_metrics)
        quality_score = round((passed_count / total) * 100) if total > 0 else 0

        # Step 4: LLM provides FEEDBACK ONLY (not judgment)
        feedback = ""
        top_issues = []

        if failed_metrics:
            # Build a simple summary for the LLM
            fail_summary = []
            for j in metric_judgments:
                if j['result'] == 'FAIL':
                    fail_summary.append(f"- {j['metric']}: measured {j['measured_value']}, threshold {j['comparison']}{j['threshold']}")

            try:
                fb_response = chat(
                    model=self.model,
                    messages=[
                        {
                            'role': 'system',
                            'content': 'You are a code quality advisor. Give specific, actionable fix suggestions in 2-3 sentences. No JSON, just plain text.'
                        },
                        {
                            'role': 'user',
                            'content': f"""This code has quality issues:
```python
{code[:500]}
```

Failed metrics:
{chr(10).join(fail_summary)}

What specific changes should be made to fix these issues? Be brief and actionable."""
                        }
                    ]
                )
                feedback = fb_response.message.content.strip()[:300]
            except Exception:
                feedback = "Fix the failed metrics listed above."

            top_issues = [f"{j['metric']}: {j['measured_value']} (need {j['comparison']}{j['threshold']})" for j in metric_judgments if j['result'] == 'FAIL']

        return {
            'verdict': verdict,
            'quality_score': quality_score,
            'reasoning': f"{passed_count}/{total} metrics passed",
            'metric_judgments': metric_judgments,
            'top_issues': top_issues[:3],
            'feedback': feedback,
            'passed_metrics': passed_metrics,
            'failed_metrics': failed_metrics,
        }

    def run(self, code_file):
        """Run the full quality agent pipeline: plan -> measure -> judge."""
        with open(code_file, 'r') as f:
            code = f.read()

        plan = self.plan(code)
        measurements = self.measure(code_file, plan)
        judgment = self.judge(code, plan, measurements)

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
