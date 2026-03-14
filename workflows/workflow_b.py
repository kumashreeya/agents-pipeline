"""
Workflow B: Iterative with correctness checking
Code -> Quick Correctness Check -> [if fail and budget] -> Code -> ...
After loop: Quality -> Test -> Final Correctness -> Done
"""
from langgraph.graph import StateGraph, END
from workflows.state import PipelineState
from workflows.nodes import coding_node, quality_node, test_node, correctness_node, quick_correctness_node


def should_retry_b(state):
    iteration = state.get("iteration", 0)
    max_iter = state.get("max_iterations", 5)
    correct = state.get("correct", False)

    if iteration >= max_iter:
        print(f"  [ROUTER] Budget exhausted ({iteration}/{max_iter})")
        return "quality"

    if correct:
        print(f"  [ROUTER] Code is CORRECT, moving to quality")
        return "quality"

    print(f"  [ROUTER] Code incorrect, retrying ({iteration}/{max_iter})")
    return "code"


def build_workflow_b():
    graph = StateGraph(PipelineState)

    graph.add_node("code", coding_node)
    graph.add_node("check", quick_correctness_node)
    graph.add_node("quality", quality_node)
    graph.add_node("test", test_node)
    graph.add_node("correctness", correctness_node)

    # Flow: code -> quick check -> [retry or quality] -> test -> final correctness -> done
    graph.set_entry_point("code")
    graph.add_edge("code", "check")
    graph.add_conditional_edges("check", should_retry_b, {"code": "code", "quality": "quality"})
    graph.add_edge("quality", "test")
    graph.add_edge("test", "correctness")
    graph.add_edge("correctness", END)

    return graph.compile()
