"""
Coding Agent - Generates code and repairs it based on feedback.
"""
import json
import os
import ast
import datetime
from ollama import chat


class CodingAgent:
    def __init__(self, model='qwen2.5-coder:3b'):
        self.model = model

    def _clean_response(self, generated_code, prompt):
        if '```python' in generated_code:
            generated_code = generated_code.split('```python')[1]
        if '```' in generated_code:
            generated_code = generated_code.split('```')[0]
        generated_code = generated_code.strip()

        func_name = None
        for line in prompt.split('\n'):
            if line.strip().startswith('def '):
                func_name = line.strip().split('(')[0].replace('def ', '')
                break

        if not func_name:
            return prompt + '\n' + generated_code + '\n'

        lines = generated_code.split('\n')
        def_lines = [i for i, l in enumerate(lines) if l.strip().startswith(f'def {func_name}(')]

        if len(def_lines) == 0:
            body_lines = []
            for line in lines:
                if line.strip() == '':
                    body_lines.append('')
                elif not line.startswith('    ') and not line.startswith('\t'):
                    body_lines.append('    ' + line)
                else:
                    body_lines.append(line)
            return prompt + '\n'.join(body_lines) + '\n'

        elif len(def_lines) >= 1:
            last_def = def_lines[-1]
            body_start = last_def + 1
            in_docstring = False
            docstring_quotes = None

            for i in range(last_def + 1, len(lines)):
                line = lines[i].strip()
                if not in_docstring:
                    if line.startswith('"""') or line.startswith("'''"):
                        docstring_quotes = line[:3]
                        if line.count(docstring_quotes) >= 2:
                            body_start = i + 1
                            continue
                        else:
                            in_docstring = True
                            continue
                    elif line and not line.startswith('#'):
                        body_start = i
                        break
                else:
                    if docstring_quotes and docstring_quotes in line:
                        in_docstring = False
                        body_start = i + 1
                        continue

            body_lines = lines[body_start:]
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()

            if body_lines:
                final_lines = []
                for line in body_lines:
                    if line.strip() == '':
                        final_lines.append('')
                    elif not line.startswith('    ') and not line.startswith('\t'):
                        final_lines.append('    ' + line)
                    else:
                        final_lines.append(line)
                return prompt + '\n'.join(final_lines) + '\n'

        return prompt + generated_code + '\n'

    def _deduplicate_functions(self, code, func_name):
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code

        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                has_body = False
                for child in node.body:
                    if isinstance(child, ast.Expr) and isinstance(child.value, (ast.Constant, ast.Str)):
                        continue
                    if isinstance(child, ast.Pass):
                        continue
                    has_body = True
                    break
                definitions.append({'node': node, 'has_body': has_body})

        if len(definitions) <= 1:
            return code

        lines = code.split('\n')
        keep_def = None
        for d in reversed(definitions):
            if d['has_body']:
                keep_def = d['node']
                break
        if keep_def is None:
            keep_def = definitions[-1]['node']

        import_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if line not in import_lines:
                    import_lines.append(line)
            elif stripped.startswith('def '):
                break

        start = keep_def.lineno - 1
        end = keep_def.end_lineno if hasattr(keep_def, 'end_lineno') and keep_def.end_lineno else len(lines)
        func_lines = lines[start:end]

        result = '\n'.join(import_lines)
        if import_lines:
            result += '\n\n\n'
        result += '\n'.join(func_lines) + '\n'
        return result

    def _validate_code(self, code):
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False, "syntax_error"
        func_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in func_names:
                    return False, f"duplicate_function:{node.name}"
                func_names.append(node.name)
        return True, "ok"

    def generate(self, task_id, prompt, feedback=None, previous_code=None, iteration=1):
        """Generate or repair code based on feedback."""

        if feedback and previous_code and iteration > 1:
            # REPAIR MODE: Give the model its own code + specific feedback
            messages = [
                {
                    'role': 'system',
                    'content': 'You are a Python expert. You will fix code based on feedback. Return ONLY the complete fixed function. No markdown. No explanations.'
                },
                {
                    'role': 'user',
                    'content': f'Here is a Python function that needs fixing:\n\n```python\n{previous_code}\n```\n\nPROBLEMS TO FIX:\n{feedback}\n\nWrite the COMPLETE fixed function. Return ONLY Python code, nothing else.'
                }
            ]
        else:
            # GENERATE MODE: First attempt
            messages = [
                {
                    'role': 'system',
                    'content': 'You are a Python coding expert. Complete the given function. Return ONLY the implementation code. No markdown. No explanations.'
                },
                {
                    'role': 'user',
                    'content': f'Complete this Python function. Write ONLY the body:\n\n{prompt}'
                }
            ]

        response = chat(model=self.model, messages=messages)
        generated_code = response.message.content.strip()

        # Clean and combine
        full_code = self._clean_response(generated_code, prompt)

        # Validate and deduplicate
        valid, issue = self._validate_code(full_code)
        if not valid and "duplicate_function" in issue:
            func_name = issue.split(":")[1]
            full_code = self._deduplicate_functions(full_code, func_name)
            valid, issue = self._validate_code(full_code)

        return {
            'timestamp': datetime.datetime.now().isoformat(),
            'task_id': task_id,
            'model': self.model,
            'prompt': prompt,
            'generated_body': generated_code,
            'full_code': full_code,
            'valid': valid,
            'validation_issue': issue,
            'iteration': iteration,
            'had_feedback': feedback is not None,
        }

    def generate_and_save(self, task_id, prompt, output_dir='results', feedback=None, previous_code=None, iteration=1):
        result = self.generate(task_id, prompt, feedback, previous_code, iteration)

        task_dir = os.path.join(output_dir, task_id.replace('/', '_'))
        os.makedirs(task_dir, exist_ok=True)

        code_file = os.path.join(task_dir, 'generated_code.py')
        with open(code_file, 'w') as f:
            f.write(result['full_code'])

        log_file = os.path.join(task_dir, 'coding_log.json')
        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        result['code_file'] = code_file
        result['log_file'] = log_file
        return result
