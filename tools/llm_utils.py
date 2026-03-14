"""Shared LLM utilities — retry logic, JSON parsing."""
import json
import time
from ollama import chat
from config import TEMPERATURE


def chat_with_retry(model, messages, max_retries=2, options=None):
    """Call Ollama with retry on failure."""
    opts = options or {'temperature': TEMPERATURE}
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            response = chat(model=model, messages=messages, options=opts)
            return response
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(1)
                continue
    raise last_error


def parse_json_response(text, max_retries=1, model=None, messages=None):
    """Parse JSON from LLM response with cleanup and retry."""

    # Clean markdown
    cleaned = text.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```python'):
        cleaned = cleaned[9:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Try parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    start = cleaned.find('{')
    end = cleaned.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(cleaned[start:end+1])
        except json.JSONDecodeError:
            pass

    # Retry with LLM if we have model and messages
    if max_retries > 0 and model and messages:
        retry_messages = messages + [
            {'role': 'assistant', 'content': text},
            {'role': 'user', 'content': 'Your response was not valid JSON. Please respond with ONLY a valid JSON object, nothing else.'}
        ]
        try:
            response = chat_with_retry(model, retry_messages)
            return parse_json_response(response.message.content, max_retries=0)
        except Exception:
            pass

    return None
