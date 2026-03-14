from ollama import chat

response = chat(
    model='qwen2.5-coder:3b',
    messages=[
        {
            'role': 'user',
            'content': 'What are the 3 biggest security risks in Python code? Answer in 3 short bullet points.'
        }
    ]
)

print(response.message.content)
