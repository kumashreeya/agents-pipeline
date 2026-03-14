"""
Configuration for the thesis pipeline.
Change PROFILE to switch between Mac development and GPU server.
"""

# ============================================
# CHANGE THIS ONE LINE TO SWITCH ENVIRONMENTS
# ============================================
PROFILE = "mac"  # "mac" or "gpu"


# ============================================
# PROFILES
# ============================================
PROFILES = {
    "mac": {
        "model": "qwen2.5-coder:3b",
        "model_provider": "ollama",
        "ollama_host": "http://localhost:11434",
        "temperature": 0,
        "max_iterations": 3,
        "run_mutation": False,
        "mutation_timeout": 60,
    },
    "gpu": {
        "model": "Qwen/Qwen3-Coder-30B-A3B-Instruct",
        "model_provider": "vllm",
        "vllm_host": "http://localhost:8000",
        "temperature": 0,
        "max_iterations": 5,
        "run_mutation": True,
        "mutation_timeout": 300,
    },
}


def get_config():
    """Get current configuration."""
    return PROFILES[PROFILE]


# Quick access
CONFIG = get_config()
MODEL = CONFIG["model"]
TEMPERATURE = CONFIG["temperature"]
MAX_ITERATIONS = CONFIG["max_iterations"]
