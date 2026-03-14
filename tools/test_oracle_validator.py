"""
Test Oracle Validator — checks if AI-generated tests match docstring examples.
Detects when the AI writes tests that pass on wrong behavior.
"""
import ast
import re


def extract_docstring_examples(code):
    """Extract >>> examples from function docstrings."""
    examples = []
    in_docstring = False
    current_input = None

    for line in code.split('\n'):
        stripped = line.strip()

        if '>>>' in stripped:
            # Extract the expression after >>>
            expr = stripped.split('>>>', 1)[1].strip()
            current_input = expr
        elif current_input is not None and stripped and not stripped.startswith('>>>') and not stripped.startswith('"""') and not stripped.startswith("'''"):
            # This line is the expected output
            expected = stripped
            examples.append({
                'input': current_input,
                'expected_output': expected,
            })
            current_input = None

    return examples


def extract_test_assertions(test_code, function_name):
    """Extract assertions from test code."""
    assertions = []

    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return assertions

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
            test_name = node.name
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    try:
                        assertion_text = ast.get_source_segment(test_code, child)
                        if assertion_text:
                            assertions.append({
                                'test_name': test_name,
                                'assertion': assertion_text,
                            })
                    except:
                        pass

    return assertions


def validate_test_oracle(code, test_code, function_name):
    """
    Validate that AI-generated tests are consistent with docstring examples.
    Returns validation results with specific findings.
    """
    result = {
        'metric': 'test_oracle_validation',
        'docstring_examples': 0,
        'test_assertions': 0,
        'validated': 0,
        'mismatched': 0,
        'coverage_of_examples': 0,
        'issues': [],
    }

    # Extract docstring examples
    examples = extract_docstring_examples(code)
    result['docstring_examples'] = len(examples)

    if not examples:
        result['issues'].append('No docstring examples found to validate against')
        return result

    # Extract test assertions
    assertions = extract_test_assertions(test_code, function_name)
    result['test_assertions'] = len(assertions)

    if not assertions:
        result['issues'].append('No test assertions found')
        return result

    # Try to execute docstring examples and compare
    # First, exec the code to get the function
    try:
        exec_globals = {}
        exec(code, exec_globals)
        func = exec_globals.get(function_name)
        if not func:
            result['issues'].append(f'Function {function_name} not found after exec')
            return result
    except Exception as e:
        result['issues'].append(f'Could not exec code: {str(e)[:100]}')
        return result

    # Run each docstring example
    example_results = []
    for ex in examples:
        try:
            actual = eval(ex['input'], exec_globals)
            expected = eval(ex['expected_output'], exec_globals)
            matches = actual == expected
            example_results.append({
                'input': ex['input'],
                'expected': str(expected),
                'actual': str(actual),
                'matches': matches,
            })
            if matches:
                result['validated'] += 1
            else:
                result['mismatched'] += 1
                result['issues'].append(f"Docstring says {ex['input']} = {expected}, but code returns {actual}")
        except Exception as e:
            result['issues'].append(f"Could not evaluate example '{ex['input']}': {str(e)[:80]}")

    result['example_results'] = example_results

    # Check if tests cover the docstring examples
    # Simple heuristic: check if assertion text contains the expected output
    covered_examples = 0
    for ex in examples:
        expected_str = ex['expected_output'].strip()
        for assertion in assertions:
            if expected_str in assertion.get('assertion', ''):
                covered_examples += 1
                break

    result['coverage_of_examples'] = round(covered_examples / len(examples) * 100, 1) if examples else 0

    return result
