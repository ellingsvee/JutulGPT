from langgraph.graph import END, START, StateGraph

from jutulgpt.edges import decide_to_finish
from jutulgpt.nodes.check_code import code_check
from jutulgpt.nodes.generate import generate
from jutulgpt.nodes.reflect import reflect
from jutulgpt.state import GraphState

builder = StateGraph(GraphState)

builder.add_node("generate", generate)
builder.add_node("check_code", code_check)
builder.add_node("reflect", reflect)

builder.add_edge(START, "generate")
builder.add_edge("generate", "check_code")
builder.add_conditional_edges(
    "check_code",
    decide_to_finish,
    {
        "end": END,
        "reflect": "reflect",
        "generate": "generate",
    },
)
builder.add_edge("reflect", "generate")

graph = builder.compile()
