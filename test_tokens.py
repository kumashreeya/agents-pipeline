"""Test that token counting works."""
from ollama import chat
from tools.token_counter import counter

response = chat(
    model='qwen2.5-coder:3b',
    messages=[{'role': 'user', 'content': 'Write a Python function that adds two numbers.'}]
)

# Check what fields the response has
print("Response type:", type(response))
print("Response fields:", dir(response))

# Try to get token counts
prompt_tokens = getattr(response, 'prompt_eval_count', 'not found')
completion_tokens = getattr(response, 'eval_count', 'not found')
print(f"Prompt tokens: {prompt_tokens}")
print(f"Completion tokens: {completion_tokens}")

# Record it
counter.record(response, agent_name="test", purpose="test call")
print(f"\nCounter summary: {counter.summary()}")
