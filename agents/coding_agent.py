"""
Coding Agent - Takes a problem description and generates code using the SLM.
"""
import json
import os
import datetime
from ollama import chat


class CodingAgent:
    """Generates code for a given problem using the SLM."""

    def __init__(self, model='qwen2.5-coder:3b'):
        self.model = model

    def generate(self, task_id, prompt):
        """
        Generate code for a given problem.
        
        Args:
            task_id: The problem ID (e.g., "HumanEval/0")
            prompt: The function signature and docstring
        
        Returns:
            Dictionary with generated code and metadata
        """
        response = chat(
            model=self.model,
            messages=[
                {
                    'role': 'system',
                    'content': 'You are a Python coding expert. Complete the given function. Return ONLY the function body code, no explanations, no markdown, no ```python blocks. Just the indented code that goes inside the function.'
                },
                {
                    'role': 'user',
                    'content': f'Complete this Python function. Return ONLY the function body:\n\n{prompt}'
                }
            ]
        )

        generated_code = response.message.content

        # Clean up the response - remove markdown if present
        if '```python' in generated_code:
            generated_code = generated_code.split('```python')[1]
            if '```' in generated_code:
                generated_code = generated_code.split('```')[0]
        elif '```' in generated_code:
            generated_code = generated_code.split('```')[1]
            if '```' in generated_code:
                generated_code = generated_code.split('```')[0]

        # Build the complete code (prompt + generated body)
        full_code = prompt + generated_code

        result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'task_id': task_id,
            'model': self.model,
            'prompt': prompt,
            'generated_body': generated_code,
            'full_code': full_code,
        }

        return result

    def generate_and_save(self, task_id, prompt, output_dir='results'):
        """Generate code and save it to a file."""
        result = self.generate(task_id, prompt)

        # Create output directory
        task_dir = os.path.join(output_dir, task_id.replace('/', '_'))
        os.makedirs(task_dir, exist_ok=True)

        # Save the generated code
        code_file = os.path.join(task_dir, 'generated_code.py')
        with open(code_file, 'w') as f:
            f.write(result['full_code'])

        # Save metadata
        log_file = os.path.join(task_dir, 'coding_log.json')
        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)

        result['code_file'] = code_file
        result['log_file'] = log_file

        return result
