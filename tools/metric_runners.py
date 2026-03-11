"""
Quality metric measurement functions.
Each function runs one tool and returns structured results.
"""
import subprocess
import json


def measure_lint(code_file):
    """Run ruff linter. Returns lint violation count and details."""
    result = subprocess.run(['ruff', 'check', code_file, '--output-format', 'json'], capture_output=True, text=True)
    issues = json.loads(result.stdout) if result.stdout else []
    return {
        'metric': 'lint_violations',
        'total': len(issues),
        'details': [{'line': i['location']['row'], 'message': i['message']} for i in issues[:10]]
    }


def measure_security(code_file):
    """Run bandit security scanner. Returns vulnerability counts by severity."""
    result = subprocess.run(['bandit', '-f', 'json', '-q', code_file], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    findings = data.get('results', [])
    return {
        'metric': 'security_vulnerabilities',
        'high': len([f for f in findings if f['issue_severity'] == 'HIGH']),
        'medium': len([f for f in findings if f['issue_severity'] == 'MEDIUM']),
        'low': len([f for f in findings if f['issue_severity'] == 'LOW']),
        'total': len(findings),
        'details': [{'severity': f['issue_severity'], 'description': f['issue_text'], 'line': f['line_number'], 'cwe': f.get('issue_cwe', {}).get('id', '')} for f in findings]
    }


def measure_complexity(code_file):
    """Run radon cyclomatic complexity. Returns per-function complexity."""
    result = subprocess.run(['radon', 'cc', code_file, '-j'], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    functions = []
    for filename, items in data.items():
        for item in items:
            functions.append({'name': item['name'], 'complexity': item['complexity'], 'rank': item['rank']})
    avg = sum(f['complexity'] for f in functions) / len(functions) if functions else 0
    return {
        'metric': 'cyclomatic_complexity',
        'functions': functions,
        'average': round(avg, 2),
        'max': max((f['complexity'] for f in functions), default=0)
    }


def measure_maintainability(code_file):
    """Run radon maintainability index. Returns MI score."""
    result = subprocess.run(['radon', 'mi', code_file, '-j'], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, score in data.items():
        if isinstance(score, dict):
            return {'metric': 'maintainability_index', 'score': round(score.get('mi', 0), 2), 'rank': score.get('rank', '?')}
        return {'metric': 'maintainability_index', 'score': round(score, 2) if isinstance(score, (int, float)) else 0, 'rank': '?'}
    return {'metric': 'maintainability_index', 'score': 0, 'rank': '?'}


def measure_types(code_file):
    """Run mypy strict type checking. Returns type error count."""
    result = subprocess.run(['mypy', '--strict', '--no-error-summary', code_file], capture_output=True, text=True)
    errors = [line for line in result.stdout.split('\n') if 'error:' in line]
    return {
        'metric': 'type_errors',
        'total_errors': len(errors),
        'details': errors[:10]
    }


def measure_halstead(code_file):
    """Run radon Halstead metrics. Returns difficulty, effort, volume, estimated bugs."""
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
        return {
            'metric': 'halstead_difficulty',
            'difficulty': round(t.get('difficulty', 0), 2),
            'effort': round(t.get('effort', 0), 2),
            'volume': round(t.get('volume', 0), 2),
            'bugs': round(t.get('bugs', 0), 4)
        }
    return {'metric': 'halstead_difficulty', 'difficulty': 0, 'effort': 0, 'volume': 0, 'bugs': 0}


def measure_sloc(code_file):
    """Run radon raw metrics. Returns LOC, SLOC, comments, blanks."""
    result = subprocess.run(['radon', 'raw', code_file, '-j'], capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout else {}
    for filename, metrics in data.items():
        return {
            'metric': 'sloc',
            'loc': metrics.get('loc', 0),
            'sloc': metrics.get('sloc', 0),
            'comments': metrics.get('comments', 0),
            'blank': metrics.get('blank', 0)
        }
    return {'metric': 'sloc', 'loc': 0, 'sloc': 0, 'comments': 0, 'blank': 0}


# Map metric names to functions
ALL_METRICS = {
    'lint_violations': measure_lint,
    'security_vulnerabilities': measure_security,
    'cyclomatic_complexity': measure_complexity,
    'maintainability_index': measure_maintainability,
    'type_errors': measure_types,
    'halstead_difficulty': measure_halstead,
    'sloc': measure_sloc,
}


def run_metric(metric_name, code_file):
    """Run a single metric by name."""
    if metric_name in ALL_METRICS:
        return ALL_METRICS[metric_name](code_file)
    return {'error': f'Unknown metric: {metric_name}'}


def run_all_metrics(code_file):
    """Run all metrics and return combined results."""
    results = {}
    for name, func in ALL_METRICS.items():
        results[name] = func(code_file)
    return results
