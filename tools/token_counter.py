"""Token counter - tracks LLM usage across the pipeline."""

class TokenCounter:
    def __init__(self):
        self.calls = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0

    def record(self, response, agent_name="unknown", purpose="unknown"):
        prompt_tokens = getattr(response, 'prompt_eval_count', 0) or 0
        completion_tokens = getattr(response, 'eval_count', 0) or 0
        total = prompt_tokens + completion_tokens
        self.calls.append({
            'agent': agent_name, 'purpose': purpose,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total,
        })
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens
        self.total_tokens += total
        self.call_count += 1

    def summary(self):
        by_agent = {}
        for call in self.calls:
            agent = call['agent']
            if agent not in by_agent:
                by_agent[agent] = {'calls': 0, 'tokens': 0}
            by_agent[agent]['calls'] += 1
            by_agent[agent]['tokens'] += call['total_tokens']
        return {
            'total_calls': self.call_count,
            'total_tokens': self.total_tokens,
            'prompt_tokens': self.total_prompt_tokens,
            'completion_tokens': self.total_completion_tokens,
            'by_agent': by_agent,
        }

    def reset(self):
        self.calls = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0

counter = TokenCounter()
