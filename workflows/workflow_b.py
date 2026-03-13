"""
Workflow B: Iterative Generate-Test-Repair
Code -> Test -> [if fail and budget] -> Code (with feedback) -> ...
After loop: Quality -> Correctness -> Done
This is what LLMLOOP, SEIDR, and ~7 papers do.
"""
from langgraph.graph import StateGraph, END
from workflows.state import PipelineState
from workflows.nodes import coding_node, quality_node, test_node, correctness_node


def should_retry_b(state):
    """Decide whether to retry coding based on test results."""
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 5)
    pass_rate = state.get("test_pass_rate", 0)
    
    if iteration >= max_iter:
        print(f"  [ROUTER] Budget exhausted ({iteration}/{max_iter})")
        return "quality"
    
    if pass_rate >= 0.8:
        print(f"  [ROUTER] Tests good enough ({pass_rate}), moving to quality")
        return "quality"
    
    print(f"  [ROUTER] Tests poor ({pass_rate}), retrying code ({iteration}/{max_iter})")
    return "code"


def build_workflow_b():
    graph = StateGraph(PipelineState)
    
    # Add nodes
    graph.add_node("code", coding_node)
    graph.add_node("test", test_node)
    graph.add_node("quality", quality_node)
    graph.add_node("correctness", correctness_node)
    
    # Flow: code -> test -> [retry or quality] -> correctness -> done
    graph.set_entry_point("code")
    graph.add_edge("code", "test")
    graph.add_conditional_edges("test", should_retry_b, {"code": "code", "quality": "quality"})
    graph.add_edge("quality", "correctness")
    graph.add_edge("correctness", END)
    
    return graph.compile()
