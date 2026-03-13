"""
Workflow A: Sequential (Baseline)
Code -> Quality -> Test -> Correctness -> Done
No iteration. Single pass. This is what ~32 papers do.
"""
from langgraph.graph import StateGraph, END
from workflows.state import PipelineState
from workflows.nodes import coding_node, quality_node, test_node, correctness_node


def build_workflow_a():
    graph = StateGraph(PipelineState)
    
    # Add nodes
    graph.add_node("code", coding_node)
    graph.add_node("quality", quality_node)
    graph.add_node("test", test_node)
    graph.add_node("correctness", correctness_node)
    
    # Linear flow: code -> quality -> test -> correctness -> done
    graph.set_entry_point("code")
    graph.add_edge("code", "quality")
    graph.add_edge("quality", "test")
    graph.add_edge("test", "correctness")
    graph.add_edge("correctness", END)
    
    return graph.compile()
