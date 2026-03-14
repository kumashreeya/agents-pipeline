"""
Autonomous Quality Agent — hybrid AST + LLM planning.
Phase 1 (PLAN): AST analysis detects patterns, LLM confirms and adjusts
Phase 2 (MEASURE): Tools run deterministically
Phase 3 (JUDGE): Code compares numbers, LLM provides feedback
"""
import json
import datetime
from ollama import chat
from tools.metric_runners import ALL_METRICS, run_metric
from tools.code_analyzer import analyze_code
from config import MODEL, TEMPERATURE


DEFAULT_THRESHOLDS = {
    'lint_violations': {'field': 'total', 'op': '<=', 'value': 5, 'desc': 'Max 5 lint violations'},
    'security_vulnerabilities': {'field': 'high', 'op': '==', 'value': 0, 'desc': 'Zero HIGH severity'},
    'cyclomatic_complexity': {'field': 'average', 'op': '<=', 'value': 10, 'desc': 'Avg complexity <= 10'},
    'maintainability_index': {'field': 'score', 'op': '>=', 'value': 20, 'desc': 'MI >= 20'},
    'type_errors': {'field': 'total_errors', 'op': '<=', 'value': 5, 'desc': 'Max 5 type errors'},
    'halstead_difficulty': {'field': 'difficulty', 'op': '<=', 'value': 30, 'desc': 'Difficulty <= 30'},
    'sloc': {'field': 'sloc', 'op': '<=', 'value': 200, 'desc': 'SLOC <= 200'},
}


class QualityAgent:
    def __init__(self, model=None):
        self.model = model or MODEL

    def plan(self, code):
        """Phase 1: Hybrid AST + LLM planning."""

        # Step 1: AST analysis (deterministic, fast, accurate)
        analysis = analyze_code(code)

        # Step 2: Build the metric selection from AST recommendations
        selected = []
        skipped = []
        for metric, reason in analysis['recommended_metrics']:
            priority = 'critical' if 'CRITICAL' in reason else 'important'
            selected.append({
                'metric': metric,
                'why': reason,
                'priority': priority,
                'source': 'code_analysis',
            })
        for metric, reason in analysis['skip_metrics']:
            skipped.append({
                'metric': metric,
                'why_skipped': reason,
                'source': 'code_analysis',
            })

        # Step 3: LLM reviews and can add/adjust (but doesn't start from scratch)
        try:
            response = chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a code quality expert. Review the automated analysis and add any insights the analysis missed. Be brief.'
                    },
                    {
                        'role': 'user',
                        'content': f"""Automated code analysis found:
- Security risks: {analysis['has_security_risks']} {analysis['security_patterns']}
- Loops: {analysis['has_loops']}, Nested conditions: {analysis['has_nested_conditions']}
- Nesting depth: {analysis['nesting_depth']}
- Type hints: {analysis['has_type_hints']}
- File I/O: {analysis['has_file_io']}
- Lines: {analysis['line_count']}
- Complex: {analysis['is_complex']}, Simple: {analysis['is_simple']}

Selected metrics: {[m['metric'] for m in selected]}
Skipped metrics: {[s['metric'] for s in skipped]}

Code snippet:
```python
{code[:300]}
```

Respond with ONLY JSON:
{{
    "code_purpose": "one sentence",
    "risk_level": "low or medium or high",
    "analysis_correct": true or false,
    "additional_concerns": ["any issues the analysis missed"]
}}"""
                    }
                ],
                options={'temperature': TEMPERATURE}
            )

            text = response.message.content.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1]
            if '```' in text:
                text = text.split('```')[0]

            try:
                llm_review = json.loads(text)
            except json.JSONDecodeError:
                llm_review = {'code_purpose': 'unknown', 'risk_level': 'medium', 'analysis_correct': True}

        except Exception:
            llm_review = {'code_purpose': 'unknown', 'risk_level': 'medium', 'analysis_correct': True}

        plan = {
            'code_purpose': llm_review.get('code_purpose', 'unknown'),
            'dangerous_patterns_found': analysis['security_patterns'],
            'risk_level': llm_review.get('risk_level', 'medium'),
            'code_analysis': {
                'nesting_depth': analysis['nesting_depth'],
                'has_loops': analysis['has_loops'],
                'has_type_hints': analysis['has_type_hints'],
                'is_complex': analysis['is_complex'],
                'line_count': analysis['line_count'],
            },
            'selected_metrics': selected,
            'skipped_metrics': skipped,
            'llm_review': llm_review,
        }

        return plan

    def measure(self, code_file, plan):
        """Phase 2: Run selected metrics deterministically."""
        measurements = {}
        for metric_info in plan.get('selected_metrics', []):
            metric_name = metric_info.get('metric', '')
            if metric_name in ALL_METRICS:
                measurements[metric_name] = run_metric(metric_name, code_file)
        return measurements

    def _compare(self, value, op, threshold):
        if op == '<=': return value <= threshold
        if op == '>=': return value >= threshold
        if op == '==': return value == threshold
        if op == '<':  return value < threshold
        if op == '>':  return value > threshold
        return True

    def judge(self, code, plan, measurements):
        """Phase 3: Deterministic comparison + LLM feedback."""
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

                metric_judgments.append({
                    'metric': metric_name,
                    'measured_value': value,
                    'threshold': thresh,
                    'comparison': op,
                    'result': 'PASS' if passed else 'FAIL',
                    'priority': metric_info.get('priority', 'important'),
                    'description': threshold_info['desc'],
                })

                if passed:
                    passed_metrics.append(metric_name)
                else:
                    failed_metrics.append(metric_name)

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

        total = len(metric_judgments)
        passed_count = len(passed_metrics)
        quality_score = round((passed_count / total) * 100) if total > 0 else 0

        feedback = ""
        top_issues = []

        if failed_metrics:
            fail_summary = []
            for j in metric_judgments:
                if j['result'] == 'FAIL':
                    fail_summary.append(f"- {j['metric']}: measured {j['measured_value']}, threshold {j['comparison']}{j['threshold']}")

            try:
                fb_response = chat(
                    model=self.model,
                    messages=[
                        {'role': 'system', 'content': 'Give specific fix suggestions in 2-3 sentences. No JSON, plain text.'},
                        {'role': 'user', 'content': f"Code issues:\n{chr(10).join(fail_summary)}\n\nWhat specific changes to fix these?"}
                    ],
                    options={'temperature': TEMPERATURE}
                )
                feedback = fb_response.message.content.strip()[:300]
            except Exception:
                feedback = "Fix the failed metrics."

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
