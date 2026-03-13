"""Shared state for all workflow variants."""
from typing import TypedDict


class PipelineState(TypedDict):
    task_id: str
    prompt: str
    entry_point: str
    code: str
    code_file: str
    syntax_valid: bool
    quality_verdict: str
    quality_score: int
    quality_feedback: str
    quality_plan: dict
    quality_measurements: dict
    test_pass_rate: float
    test_coverage: float
    test_total: int
    test_passed: int
    test_smells: int
    test_flaky: bool
    correct: bool
    iteration: int
    max_iterations: int
    total_tokens: int
    ai_dead_code: int
    ai_hallucinated_imports: int
    ai_duplicates: int
