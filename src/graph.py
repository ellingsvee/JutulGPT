from langgraph.graph import StateGraph, END, START
from schema import GraphState
from nodes.generate import generate
from nodes.check_code import code_check
from nodes.reflect import reflect
from edges import decide_to_finish

workflow = StateGraph(GraphState)

workflow.add_node("generate", generate)
workflow.add_node("check_code", code_check)
workflow.add_node("reflect", reflect)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "check_code")
workflow.add_conditional_edges(
    "check_code",
    decide_to_finish,
    {
        "end": END,
        "reflect": "reflect",
        "generate": "generate",
    },
)
workflow.add_edge("reflect", "generate")

app = workflow.compile()
