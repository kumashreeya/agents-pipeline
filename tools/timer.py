"""Per-agent timing for cost analysis."""
import time


class AgentTimer:
    def __init__(self):
        self.timings = {}

    def start(self, agent_name):
        self.timings[agent_name] = {'start': time.time(), 'elapsed': 0}

    def stop(self, agent_name):
        if agent_name in self.timings:
            self.timings[agent_name]['elapsed'] = round(time.time() - self.timings[agent_name]['start'], 2)

    def get(self, agent_name):
        return self.timings.get(agent_name, {}).get('elapsed', 0)

    def summary(self):
        return {k: v['elapsed'] for k, v in self.timings.items()}

    def reset(self):
        self.timings = {}

timer = AgentTimer()
