from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from jutulgpt.config import max_iterations
from jutulgpt.nodes import check_code, generate_code, retrieve_info
from jutulgpt.state import GraphState
from jutulgpt.tools import (
    retrieve_jutuldarcy_documentation,
    retrieve_jutuldarcy_examples,
)
from jutulgpt.utils import logger

generate_code_name = "generate_code"
check_code_name = "check_code"
retrieve_info_name = "retrieve_info"
retrieve_documentation_name = "retrieve_docs"
retrieve_examples_name = "retrieve_examples"
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
builder.add_node(retrieve_info_name, retrieve_info)


builder.add_edge(START, retrieve_info_name)
builder.add_edge(retrieve_info_name, generate_code_name)
builder.add_edge(generate_code_name, check_code_name)
builder.add_conditional_edges(
    check_code_name,
    decide_to_finish,
    {
        end_name: END,
        generate_code_name: generate_code_name,
        # generate_code_name: retrieve_info_name,  # Retry by retrieving info again
    },
)
graph = builder.compile()

# Plot the graph
graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
