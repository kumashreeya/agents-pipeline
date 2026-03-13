"""
Coding Agent - Takes a problem description and generates code using the SLM.
"""
import json
import os
import ast
import datetime
from ollama import chat


class CodingAgent:
    """Generates code for a given problem using the SLM."""

    def __init__(self, model='qwen2.5-coder:3b'):
        self.model = model

    def _clean_response(self, generated_code, prompt):
        """Clean up the model's response and extract only the function body."""
        
        # Step 1: Remove markdown blocks
        if '```python' in generated_code:
            generated_code = generated_code.split('```python')[1]
        if '```' in generated_code:
            generated_code = generated_code.split('```')[0]
        generated_code = generated_code.strip()

        # Step 2: Get the function name from the prompt
        func_name = None
        for line in prompt.split('\n'):
            if line.strip().startswith('def '):
                func_name = line.strip().split('(')[0].replace('def ', '')
                break

        if not func_name:
            return prompt + '\n' + generated_code + '\n'

        # Step 3: Check if the model repeated the full function
        # Try to parse what the model returned
        lines = generated_code.split('\n')
        
        # Find if there's a "def func_name(" line in the response
        def_lines = []
        for i, line in enumerate(lines):
            if line.strip().startswith(f'def {func_name}('):
                def_lines.append(i)

        if len(def_lines) == 0:
            # Model returned just the body — perfect, just combine
            # Make sure body is indented
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
            # Model repeated the function — extract the LAST complete definition
            # The last def is most likely to have the actual implementation
            last_def = def_lines[-1]
            
            # Find the body after the last def
            # Skip past the docstring if present
            body_start = last_def + 1
            in_docstring = False
            docstring_quotes = None
            
            for i in range(last_def + 1, len(lines)):
                line = lines[i].strip()
                
                if not in_docstring:
                    if line.startswith('"""') or line.startswith("'''"):
                        docstring_quotes = line[:3]
                        if line.count(docstring_quotes) >= 2:
                            # Single-line docstring
                            body_start = i + 1
                            continue
                        else:
                            in_docstring = True
                            continue
                    elif line and not line.startswith('#'):
                        # Found the actual body
                        body_start = i
                        break
                else:
                    if docstring_quotes and docstring_quotes in line:
                        in_docstring = False
                        body_start = i + 1
                        continue

            # Extract body lines from body_start to end
            body_lines = lines[body_start:]
            
            # Remove trailing empty lines
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()

            if body_lines:
                body = '\n'.join(body_lines)
                # Make sure body is indented
                final_lines = []
                for line in body_lines:
                    if line.strip() == '':
                        final_lines.append('')
                    elif not line.startswith('    ') and not line.startswith('\t'):
                        final_lines.append('    ' + line)
                    else:
                        final_lines.append(line)
                return prompt + '\n'.join(final_lines) + '\n'

        # Fallback: just use prompt + generated
        return prompt + generated_code + '\n'

    def _validate_code(self, code):
        """Check if code compiles and has no duplicate functions."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return False, "syntax_error"
        
        # Check for duplicate function names
        func_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in func_names:
                    return False, f"duplicate_function:{node.name}"
                func_names.append(node.name)
        
        return True, "ok"

    def generate(self, task_id, prompt):
        """Generate code for a given problem."""
        response = chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a Python coding expert. Complete the given function. Return ONLY the implementation code that goes inside the function body. Do not repeat the function signature or docstring. No markdown. No explanations. Just indented Python code.'
                },
                {
                    'role': 'user',
                    'content': f'Complete this Python function. Write ONLY the body:\n\n{prompt}'
                }
            ]
        )

        generated_code = response.message.content.strip()

        # Clean and combine with prompt
        full_code = self._clean_response(generated_code, prompt)

        # Validate
        valid, issue = self._validate_code(full_code)
        
        # If still has duplicates, try harder to fix
        if not valid and "duplicate_function" in issue:
            # Nuclear option: parse and keep only the last definition
            func_name = issue.split(":")[1]
            full_code = self._deduplicate_functions(full_code, func_name)
            valid, issue = self._validate_code(full_code)

        result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'task_id': task_id,
            'model': self.model,
            'prompt': prompt,
            'generated_body': generated_code,
            'full_code': full_code,
            'valid': valid,
            'validation_issue': issue,
        }

        return result

    def _deduplicate_functions(self, code, func_name):
        """Remove duplicate function definitions, keeping the last one with a body."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return code

        # Find all definitions of this function
        definitions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                # Check if it has a real body (not just pass or docstring)
                has_body = False
                for child in node.body:
                    if isinstance(child, ast.Expr) and isinstance(child.value, (ast.Constant, ast.Str)):
                        continue  # docstring
                    if isinstance(child, ast.Pass):
                        continue
                    has_body = True
                    break
                definitions.append({'node': node, 'has_body': has_body})

        if len(definitions) <= 1:
            return code

        # Keep the last definition that has a body
        lines = code.split('\n')
        keep_def = None
        for d in reversed(definitions):
            if d['has_body']:
                keep_def = d['node']
                break
        
        if keep_def is None:
            keep_def = definitions[-1]['node']

        # Get imports from the top of the file
        import_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                if line not in import_lines:
                    import_lines.append(line)
            elif stripped.startswith('def '):
                break
            elif stripped == '' or stripped.startswith('#'):
                continue

        # Extract the kept function (from its line to end or next def)
        start = keep_def.lineno - 1
        end = keep_def.end_lineno if hasattr(keep_def, 'end_lineno') and keep_def.end_lineno else len(lines)
        func_lines = lines[start:end]

        # Rebuild: imports + blank line + function
        result = '\n'.join(import_lines)
        if import_lines:
            result += '\n\n\n'
        result += '\n'.join(func_lines) + '\n'

        return result

    def generate_and_save(self, task_id, prompt, output_dir='results'):
        """Generate code and save it to a file."""
        result = self.generate(task_id, prompt)

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
