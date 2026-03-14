"""
AST-based code analyzer — detects patterns to help quality agent select metrics.
This removes the guesswork from the LLM's planning phase.
"""
import ast
import re


def analyze_code(code):
    """Analyze code and return detected patterns that guide metric selection."""

    result = {
        'has_security_risks': False,
        'security_patterns': [],
        'has_loops': False,
        'has_nested_conditions': False,
        'nesting_depth': 0,
        'has_type_hints': False,
        'has_file_io': False,
        'has_network': False,
        'has_external_imports': False,
        'external_imports': [],
        'function_count': 0,
        'function_names': [],
        'line_count': len(code.split('\n')),
        'is_complex': False,
        'is_simple': False,
        'recommended_metrics': [],
        'skip_metrics': [],
    }

    # Dangerous patterns (string-based — catches things AST misses)
    dangerous = {
        'eval(': 'eval function — arbitrary code execution',
        'exec(': 'exec function — arbitrary code execution',
        'pickle.load': 'pickle deserialization — arbitrary object creation',
        'os.system': 'os.system — command injection risk',
        'subprocess.call': 'subprocess — command injection risk',
        'subprocess.run': 'subprocess — command injection risk',
        'subprocess.Popen': 'subprocess — command injection risk',
        '__import__': 'dynamic import — code injection risk',
        'compile(': 'compile — code execution risk',
    }

    for pattern, description in dangerous.items():
        if pattern in code:
            result['has_security_risks'] = True
            result['security_patterns'].append(description)

    # SQL injection pattern
    if re.search(r'["\']SELECT.*\+.*["\']|["\']INSERT.*\+.*["\']|["\']DELETE.*\+.*["\']', code, re.IGNORECASE):
        result['has_security_risks'] = True
        result['security_patterns'].append('String-concatenated SQL — injection risk')

    # AST analysis
    try:
        tree = ast.parse(code)
    except SyntaxError:
        result['recommended_metrics'] = list(dangerous.keys())
        return result

    # Count functions
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            result['function_count'] += 1
            result['function_names'].append(node.name)

            # Check for type hints
            if node.returns is not None:
                result['has_type_hints'] = True
            for arg in node.args.args:
                if arg.annotation is not None:
                    result['has_type_hints'] = True

    # Check for loops and nesting
    def check_nesting(node, depth=0):
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                result['has_loops'] = True
                max_depth = max(max_depth, check_nesting(child, depth + 1))
            elif isinstance(child, (ast.If,)):
                if depth > 0:
                    result['has_nested_conditions'] = True
                max_depth = max(max_depth, check_nesting(child, depth + 1))
            else:
                max_depth = max(max_depth, check_nesting(child, depth))
        return max_depth

    result['nesting_depth'] = check_nesting(tree)

    # Check for file I/O
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = ''
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            if func_name in ('open', 'read', 'write', 'readlines'):
                result['has_file_io'] = True
            if func_name in ('connect', 'socket', 'request', 'get', 'post'):
                result['has_network'] = True

    # Check imports
    stdlib = {
        'os', 'sys', 'json', 're', 'math', 'random', 'datetime', 'time',
        'collections', 'itertools', 'functools', 'typing', 'pathlib',
        'subprocess', 'shutil', 'tempfile', 'io', 'string', 'copy',
        'ast', 'abc', 'enum', 'dataclasses', 'hashlib', 'pickle',
        'sqlite3', 'csv', 'logging', 'unittest', 'argparse',
        'statistics', 'decimal', 'fractions', 'bisect', 'heapq',
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split('.')[0]
                if mod not in stdlib:
                    result['has_external_imports'] = True
                    result['external_imports'].append(mod)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split('.')[0]
                if mod not in stdlib:
                    result['has_external_imports'] = True
                    result['external_imports'].append(mod)

    # Determine complexity
    if result['nesting_depth'] >= 3 or result['line_count'] > 50:
        result['is_complex'] = True
    elif result['nesting_depth'] <= 1 and result['line_count'] <= 15:
        result['is_simple'] = True

    # RECOMMEND metrics based on analysis
    recommended = []
    skip = []

    # Always check these
    recommended.append(('cyclomatic_complexity', 'Always relevant'))
    recommended.append(('maintainability_index', 'Always relevant'))

    # Security — based on detected patterns
    if result['has_security_risks']:
        recommended.append(('security_vulnerabilities', f"CRITICAL: found {', '.join(result['security_patterns'][:3])}"))
    else:
        skip.append(('security_vulnerabilities', 'No dangerous patterns detected in code'))

    # Lint — always useful
    recommended.append(('lint_violations', 'Always relevant for code style'))

    # Types — based on whether hints exist
    if result['has_type_hints']:
        recommended.append(('type_errors', 'Code has type hints — check consistency'))
    else:
        skip.append(('type_errors', 'No type hints in code — mypy would only report missing annotations'))

    # Halstead — for complex code
    if result['is_complex'] or result['nesting_depth'] >= 2:
        recommended.append(('halstead_difficulty', 'Complex code — error-proneness matters'))
    else:
        skip.append(('halstead_difficulty', 'Simple code — halstead not informative'))

    # SLOC — for larger code
    if result['line_count'] > 20:
        recommended.append(('sloc', 'Code is large enough for size analysis'))
    else:
        skip.append(('sloc', 'Small code — SLOC not informative'))

    result['recommended_metrics'] = recommended
    result['skip_metrics'] = skip

    return result
