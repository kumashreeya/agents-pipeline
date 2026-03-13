"""
Workflow C: Early Quality-Gated (Novel)
Code -> Quality -> [if fail and budget] -> Code (with quality feedback) -> ...
After quality passes: Test -> Correctness -> Done
Only 2 papers do quality-gated loops. This is our novel contribution.
"""
from langgraph.graph import StateGraph, END
from workflows.state import PipelineState
from workflows.nodes import coding_node, quality_node, test_node, correctness_node


def should_retry_c(state):
    """Decide whether to retry coding based on quality results."""
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 5)
    verdict = state.get("quality_verdict", "UNKNOWN")
    
    if iteration >= max_iter:
        print(f"  [ROUTER] Budget exhausted ({iteration}/{max_iter})")
        return "test"
    
    if verdict == "PASS":
        print(f"  [ROUTER] Quality PASSED, moving to tests")
        return "test"
    
    print(f"  [ROUTER] Quality {verdict}, retrying code ({iteration}/{max_iter})")
    return "code"


def build_workflow_c():
    graph = StateGraph(PipelineState)
    
    # Add nodes
    graph.add_node("code", coding_node)
    graph.add_node("quality", quality_node)
    graph.add_node("test", test_node)
    graph.add_node("correctness", correctness_node)
    
    # Flow: code -> quality -> [retry or test] -> correctness -> done
    graph.set_entry_point("code")
    graph.add_edge("code", "quality")
    graph.add_conditional_edges("quality", should_retry_c, {"code": "code", "test": "test"})
    graph.add_edge("test", "correctness")
    graph.add_edge("correctness", END)
    
    return graph.compile()
