"""
Test Agent - Generates tests for code and evaluates test quality.
"""
import subprocess
import json
import os
import re
import datetime
from ollama import chat


class TestAgent:

    def __init__(self, model='qwen2.5-coder:3b'):
        self.model = model

    def generate_tests(self, code, function_name):
        """Ask AI to write tests."""
        response = chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': f'''Write pytest tests. RULES:
- Write ONLY Python code, no markdown, no explanations
- First line must be: from generated_code import {function_name}
- Do NOT redefine the function
- Write at least 5 test functions using def test_xxx():
- Include normal, edge, boundary, and empty input cases
- Every test must have an assert statement'''
                },
                {
                    'role': 'user',
                    'content': f'Write tests for function "{function_name}":\n\n{code}'
                }
            ]
        )

        test_code = response.message.content.strip()

        # Clean markdown
        if '```python' in test_code:
            test_code = test_code.split('```python')[1]
        if '```' in test_code:
            test_code = test_code.split('```')[0]
        test_code = test_code.strip()

        # Ensure correct import
        if f'from generated_code import' not in test_code:
            test_code = f'from generated_code import {function_name}\n\n' + test_code

        # Remove function redefinition if model added one
        lines = test_code.split('\n')
        clean_lines = []
        in_func_def = False
        for line in lines:
            if line.strip().startswith(f'def {function_name}('):
                in_func_def = True
                continue
            if in_func_def:
                if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                    in_func_def = False
                else:
                    continue
            if not in_func_def:
                clean_lines.append(line)

        return '\n'.join(clean_lines).strip()

    def _run_pytest(self, test_file, extra_args=None):
        """Run pytest in the correct directory and return raw output."""
        test_dir = os.path.dirname(os.path.abspath(test_file))
        test_name = os.path.basename(test_file)
        cmd = ['python', '-m', 'pytest', test_name]
        if extra_args:
            cmd.extend(extra_args)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, cwd=test_dir
            )
            return result.stdout + '\n' + result.stderr
        except subprocess.TimeoutExpired:
            return 'TIMEOUT'

    def _parse_pytest_summary(self, output):
        """Parse pytest output to get passed/failed/error counts."""
        passed = 0
        failed = 0
        errors = 0

        # Look for summary line like "4 passed, 1 failed"
        match = re.search(r'(\d+) passed', output)
        if match:
            passed = int(match.group(1))

        match = re.search(r'(\d+) failed', output)
        if match:
            failed = int(match.group(1))

        match = re.search(r'(\d+) error', output)
        if match:
            errors = int(match.group(1))

        return passed, failed, errors

    def measure_pass_rate(self, test_file):
        """Metric 1: Test pass rate."""
        output = self._run_pytest(test_file, ['-v', '--tb=short'])

        if output == 'TIMEOUT':
            return {'metric': 'test_pass_rate', 'passed': 0, 'failed': 0, 'total': 0, 'pass_rate': 0, 'error': 'timeout'}

        passed, failed, errors = self._parse_pytest_summary(output)
        total = passed + failed + errors

        return {
            'metric': 'test_pass_rate',
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'total': total,
            'pass_rate': round(passed / total, 2) if total > 0 else 0,
            'output': output[:500]
        }

    def measure_coverage(self, test_file, code_file):
        """Metric 2: Line coverage."""
        test_dir = os.path.dirname(os.path.abspath(test_file))
        test_name = os.path.basename(test_file)

        output = self._run_pytest(test_file, ['--cov=generated_code', '--cov-report=json', '-q'])

        # Look for coverage.json in the test directory
        cov_json = os.path.join(test_dir, 'coverage.json')
        if not os.path.exists(cov_json):
            # Check project root
            cov_json = 'coverage.json'

        if os.path.exists(cov_json):
            try:
                with open(cov_json, 'r') as f:
                    cov_data = json.load(f)
                coverage = cov_data.get('totals', {}).get('percent_covered', 0)
                os.remove(cov_json)
                for f_path in [os.path.join(test_dir, '.coverage'), '.coverage']:
                    if os.path.exists(f_path):
                        os.remove(f_path)
                return {'metric': 'line_coverage', 'coverage_percent': round(coverage, 2)}
            except:
                pass

        return {'metric': 'line_coverage', 'coverage_percent': 0, 'note': 'coverage file not generated'}

    def measure_validity(self, test_file):
        """Metric 3: Are tests syntactically valid?"""
        try:
            with open(test_file, 'r') as f:
                code = f.read()
            compile(code, test_file, 'exec')
            test_count = code.count('def test_')
            assert_count = code.count('assert ')
            return {
                'metric': 'test_validity',
                'valid': True,
                'test_function_count': test_count,
                'assert_count': assert_count,
                'assertions_per_test': round(assert_count / test_count, 2) if test_count > 0 else 0
            }
        except SyntaxError as e:
            return {'metric': 'test_validity', 'valid': False, 'error': str(e)}

    def measure_smells(self, test_file):
        """Metric 4: Test smells."""
        with open(test_file, 'r') as f:
            lines = f.read().split('\n')

        smells = []

        # Check each test function
        in_test = False
        test_name = ''
        has_assert = False

        for i, line in enumerate(lines):
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
        """Metric 5: Run tests multiple times to detect inconsistency."""
        results = []
        for i in range(runs):
            output = self._run_pytest(test_file, ['-q', '--tb=no'])
            passed, _, _ = self._parse_pytest_summary(output)
            results.append(passed)

        is_flaky = len(set(results)) > 1
        max_p = max(results) if results else 0

        return {
            'metric': 'flakiness',
            'runs': results,
            'is_flaky': is_flaky,
            'flakiness_rate': round(1 - min(results) / max_p, 2) if max_p > 0 else 0
        }

    def run(self, code_file, task_id="unknown", function_name=None, output_dir='results'):
        """Run the full test agent pipeline."""

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

        # Step 1: Generate tests
        print(f"  Generating tests for '{function_name}'...")
        test_code = self.generate_tests(code, function_name)
        with open(test_file, 'w') as f:
            f.write(test_code)

        # Step 2: Validity
        print(f"  Checking validity...")
        validity = self.measure_validity(test_file)
        if not validity.get('valid'):
            return {'task_id': task_id, 'metrics': {'validity': validity}}

        # Step 3: Pass rate
        print(f"  Running tests...")
        pass_rate = self.measure_pass_rate(test_file)

        # Step 4: Coverage
        print(f"  Measuring coverage...")
        coverage = self.measure_coverage(test_file, code_file)

        # Step 5: Smells
        print(f"  Checking smells...")
        smells = self.measure_smells(test_file)

        # Step 6: Flakiness
        print(f"  Checking flakiness...")
        flakiness = self.measure_flakiness(test_file)

        all_metrics = {
            'validity': validity,
            'pass_rate': pass_rate,
            'coverage': coverage,
            'smells': smells,
            'flakiness': flakiness,
        }

        result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'task_id': task_id,
            'model': self.model,
            'code_file': code_file,
            'test_file': test_file,
            'function_name': function_name,
            'metrics': all_metrics,
        }

        log_file = os.path.join(task_dir, 'test_log.json')
        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        return result
