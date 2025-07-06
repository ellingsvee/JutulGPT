from langgraph.graph import END, START, StateGraph

from jutulgpt.config import max_iterations

from jutulgpt.nodes import check_code, generate_code
from jutulgpt.state import GraphState
from jutulgpt.utils import logger

generate_code_name = "generate_code"
check_code_name = "check_code"
start_name = "start"
end_name = "end"


def decide_to_finish(state: GraphState):
    if not state.error or state.iterations == max_iterations:
        logger.info("Decision: Finish")
        if state.iterations == max_iterations:
            print(f"Max iterations {max_iterations} reached.")
        return end_name
    logger.info("Devipcision: Retry")
    return generate_code_name


builder = StateGraph(GraphState)
builder.add_node(generate_code_name, generate_code)
builder.add_node(check_code_name, check_code)

builder.add_edge(START, generate_code_name)
builder.add_edge(generate_code_name, check_code_name)
builder.add_conditional_edges(
    check_code_name,
    decide_to_finish,
    {
        end_name: END,
        generate_code_name: generate_code_name,
    },
)
graph = builder.compile()
