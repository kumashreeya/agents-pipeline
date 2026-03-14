from tools.llm_utils import parse_json_response

# Test clean JSON
print("Test 1:", parse_json_response('{"key": "value"}'))

# Test with markdown
print("Test 2:", parse_json_response('```json\n{"key": "value"}\n```'))

# Test with extra text
print("Test 3:", parse_json_response('Here is the result: {"key": "value"} and thats it'))

# Test broken JSON (should return None)
print("Test 4:", parse_json_response('not json at all'))
