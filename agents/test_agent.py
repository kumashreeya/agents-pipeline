"""
Improved Test Agent — better prompts, import fixing, retry on errors.
"""
import subprocess
import json
import os
import re
import ast
import datetime
from ollama import chat
from config import MODEL, TEMPERATURE
from tools.mutation_score import measure_mutation_score


class TestAgent:
    def __init__(self, model=None):
        self.model = model or MODEL

    def generate_tests(self, code, function_name, retry=0):
        """Generate tests with improved prompt and retry logic."""

        # Extract function signature for the prompt
        sig = ""
        for line in code.split('\n'):
            if line.strip().startswith(f'def {function_name}('):
                sig = line.strip()
                break

        # Extract docstring examples if they exist
        examples = ""
        in_docstring = False
        for line in code.split('\n'):
            if '"""' in line or "'''" in line:
                in_docstring = not in_docstring
            if in_docstring and '>>>' in line:
                examples += line.strip() + '\n'

        prompt_extra = ""
        if examples:
            prompt_extra = f"\n\nThe function has these examples in its docstring:\n{examples}\nMake sure your tests cover these cases AND additional edge cases."

        if retry > 0:
            prompt_extra += "\n\nIMPORTANT: Your previous attempt had errors. Write simpler, more careful tests this time."

        response = chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': f'''You are a Python test engineer. Write pytest tests.

STRICT RULES:
1. First line MUST be: from generated_code import {function_name}
2. Do NOT import anything else unless absolutely needed
3. Do NOT redefine or rewrite the function being tested
4. Every test function must start with: def test_
5. Every test function must have at least one assert statement
6. Write exactly 5 test functions
7. Use simple assert statements like: assert {function_name}(input) == expected
8. NO markdown, NO explanations, ONLY Python code

EXAMPLE FORMAT:
from generated_code import {function_name}

def test_normal_case():
    assert {function_name}(...) == ...

def test_edge_case():
    assert {function_name}(...) == ...'''
                },
                {
                    'role': 'user',
                    'content': f'Write 5 pytest tests for this function:\n\n{sig}{prompt_extra}\n\nFull code:\n```python\n{code}\n```'
                }
            ],
            options={'temperature': TEMPERATURE}
        )

        test_code = response.message.content.strip()

        # Clean markdown
        if '```python' in test_code:
            test_code = test_code.split('```python')[1]
        if '```' in test_code:
            test_code = test_code.split('```')[0]
        test_code = test_code.strip()

        # Fix imports
        test_code = self._fix_imports(test_code, function_name)

        # Remove function redefinition
        test_code = self._remove_function_redefinition(test_code, function_name)

        # Remove any non-test, non-import lines at top level
        test_code = self._clean_test_code(test_code, function_name)

        # Validate syntax — retry once if broken
        try:
            compile(test_code, '<test>', 'exec')
        except SyntaxError as e:
            if retry < 1:
                print(f"  Test syntax error: {e}. Retrying...")
                return self.generate_tests(code, function_name, retry=retry+1)
            else:
                print(f"  Test syntax error after retry: {e}")

        return test_code

    def _fix_imports(self, test_code, function_name):
        """Ensure correct import line exists."""
        lines = test_code.split('\n')
        has_correct_import = False
        clean_lines = []

        for line in lines:
            # Remove wrong imports of the function
            if f'import {function_name}' in line and 'from generated_code' not in line:
                continue
            if f'from generated_code import {function_name}' in line:
                has_correct_import = True
            clean_lines.append(line)

        if not has_correct_import:
            clean_lines.insert(0, f'from generated_code import {function_name}')

        return '\n'.join(clean_lines)

    def _remove_function_redefinition(self, test_code, function_name):
        """Remove if the AI redefined the function being tested."""
        lines = test_code.split('\n')
        clean = []
        skip = False

        for line in lines:
            if line.strip().startswith(f'def {function_name}(') and 'def test_' not in line:
                skip = True
                continue
            if skip:
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    skip = False
                else:
                    continue
            if not skip:
                clean.append(line)

        return '\n'.join(clean)

    def _clean_test_code(self, test_code, function_name):
        """Remove stray code that isn't imports or test functions."""
        lines = test_code.split('\n')
        clean = []
        in_test_func = False

        for line in lines:
            stripped = line.strip()

            # Always keep import lines
            if stripped.startswith('import ') or stripped.startswith('from '):
                clean.append(line)
                in_test_func = False
                continue

            # Keep test function definitions and their bodies
            if stripped.startswith('def test_'):
                in_test_func = True
                clean.append(line)
                continue

            if in_test_func:
                if stripped == '' or line.startswith(' ') or line.startswith('\t'):
                    clean.append(line)
                else:
                    in_test_func = False
                    # Check if this is another test or something else
                    if stripped.startswith('def test_'):
                        in_test_func = True
                        clean.append(line)
                continue

            # Keep blank lines between functions
            if stripped == '':
                clean.append(line)

        return '\n'.join(clean).strip()

    def _run_pytest(self, test_file, extra_args=None):
        test_dir = os.path.dirname(os.path.abspath(test_file))
        test_name = os.path.basename(test_file)
        cmd = ['python', '-m', 'pytest', test_name]
        if extra_args:
            cmd.extend(extra_args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=test_dir)
            return result.stdout + '\n' + result.stderr
        except subprocess.TimeoutExpired:
            return 'TIMEOUT'

    def _parse_pytest(self, output):
        passed = failed = errors = 0
        m = re.search(r'(\d+) passed', output)
        if m: passed = int(m.group(1))
        m = re.search(r'(\d+) failed', output)
        if m: failed = int(m.group(1))
        m = re.search(r'(\d+) error', output)
        if m: errors = int(m.group(1))
        return passed, failed, errors

    def measure_pass_rate(self, test_file):
        output = self._run_pytest(test_file, ['-v', '--tb=short'])
        if output == 'TIMEOUT':
            return {'metric': 'test_pass_rate', 'passed': 0, 'failed': 0, 'total': 0, 'pass_rate': 0, 'error': 'timeout'}
        passed, failed, errors = self._parse_pytest(output)
        total = passed + failed + errors
        return {
            'metric': 'test_pass_rate', 'passed': passed, 'failed': failed,
            'errors': errors, 'total': total,
            'pass_rate': round(passed / total, 2) if total > 0 else 0,
            'output': output[:300]
        }

    def measure_coverage(self, test_file, code_file):
        test_dir = os.path.dirname(os.path.abspath(test_file))
        output = self._run_pytest(test_file, ['--cov=generated_code', '--cov-report=json', '-q'])
        for path in [os.path.join(test_dir, 'coverage.json'), 'coverage.json']:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = json.load(f)
                    cov = data.get('totals', {}).get('percent_covered', 0)
                    os.remove(path)
                    for cp in [os.path.join(test_dir, '.coverage'), '.coverage']:
                        if os.path.exists(cp): os.remove(cp)
                    return {'metric': 'line_coverage', 'coverage_percent': round(cov, 2)}
                except:
                    pass
        return {'metric': 'line_coverage', 'coverage_percent': 0}

    def measure_validity(self, test_file):
        try:
            with open(test_file, 'r') as f:
                code = f.read()
            compile(code, test_file, 'exec')
            tc = code.count('def test_')
            ac = code.count('assert ')
            return {
                'metric': 'test_validity', 'valid': True,
                'test_function_count': tc, 'assert_count': ac,
                'assertions_per_test': round(ac / tc, 2) if tc > 0 else 0
            }
        except SyntaxError as e:
            return {'metric': 'test_validity', 'valid': False, 'error': str(e)}

    def measure_smells(self, test_file):
        with open(test_file, 'r') as f:
            lines = f.read().split('\n')
        smells = []
        in_test = False
        test_name = ''
        has_assert = False
        for line in lines:
            if line.strip().startswith('def test_'):
                if in_test and not has_assert:
                    smells.append({'smell': 'no_assertion', 'test': test_name})
                in_test = True
                test_name = line.strip().split('(')[0].replace('def ', '')
                has_assert = False
            elif in_test and 'assert' in line:
                has_assert = True
            if line.strip() == 'pass' and in_test:
                smells.append({'smell': 'empty_test', 'test': test_name})
        if in_test and not has_assert:
            smells.append({'smell': 'no_assertion', 'test': test_name})
        return {'metric': 'test_smells', 'total_smells': len(smells), 'smells': smells}

    def measure_flakiness(self, test_file, runs=3):
        results = []
        for i in range(runs):
            output = self._run_pytest(test_file, ['-q', '--tb=no'])
            passed, _, _ = self._parse_pytest(output)
            results.append(passed)
        is_flaky = len(set(results)) > 1
        max_p = max(results) if results else 0
        return {
            'metric': 'flakiness', 'runs': results, 'is_flaky': is_flaky,
            'flakiness_rate': round(1 - min(results) / max_p, 2) if max_p > 0 else 0
        }

    def measure_mutation(self, code_file, test_file, timeout=60):
        try:
            return measure_mutation_score(code_file, test_file, timeout=timeout)
        except Exception as e:
            return {'metric': 'mutation_score', 'score': 0, 'error': str(e), 'total_mutants': 0}

    def run(self, code_file, task_id="unknown", function_name=None, output_dir='results', run_mutation=False):
        with open(code_file, 'r') as f:
            code = f.read()

        if function_name is None:
            for line in code.split('\n'):
                if line.strip().startswith('def ') and not line.strip().startswith('def _'):
                    function_name = line.strip().split('(')[0].replace('def ', '')
                    break

        task_dir = os.path.join(output_dir, task_id.replace('/', '_'))
        os.makedirs(task_dir, exist_ok=True)
        test_file = os.path.join(task_dir, 'generated_tests.py')

        print(f"  Generating tests for '{function_name}'...")
        test_code = self.generate_tests(code, function_name)
        with open(test_file, 'w') as f:
            f.write(test_code)

        print(f"  Checking validity...")
        validity = self.measure_validity(test_file)
        if not validity.get('valid'):
            return {'task_id': task_id, 'test_file': test_file, 'metrics': {'validity': validity}}

        print(f"  Running tests...")
        pass_rate = self.measure_pass_rate(test_file)

        print(f"  Measuring coverage...")
        coverage = self.measure_coverage(test_file, code_file)

        print(f"  Checking smells...")
        smells = self.measure_smells(test_file)

        print(f"  Checking flakiness...")
        flakiness = self.measure_flakiness(test_file)

        all_metrics = {
            'validity': validity,
            'pass_rate': pass_rate,
            'coverage': coverage,
            'smells': smells,
            'flakiness': flakiness,
        }

        if run_mutation:
            print(f"  Measuring mutation score...")
            mutation = self.measure_mutation(code_file, test_file, timeout=60)
            all_metrics['mutation'] = mutation

        result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'task_id': task_id, 'model': self.model,
            'code_file': code_file, 'test_file': test_file,
            'function_name': function_name, 'metrics': all_metrics,
        }

        log_file = os.path.join(task_dir, 'test_log.json')
        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        return result
