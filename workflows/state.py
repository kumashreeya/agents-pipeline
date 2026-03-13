"""
Shared state for all workflow variants.
Every node reads from and writes to this state.
"""
from typing import TypedDict, Optional


class PipelineState(TypedDict):
    # Task info
    task_id: str
    prompt: str
    entry_point: str
    
    # Code
    code: str
    code_file: str
    syntax_valid: bool
    
    # Quality results
    quality_verdict: str
    quality_score: int
    quality_feedback: str
    quality_plan: dict
    quality_measurements: dict
    
    # Test results
    test_pass_rate: float
    test_coverage: float
    test_total: int
    test_passed: int
    test_smells: int
    test_flaky: bool
    
    # Correctness
    correct: bool
    
    # Budget tracking
    iteration: int
    max_iterations: int
    total_tokens: int
