from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from jutulgpt.config import max_iterations
from jutulgpt.nodes import check_code, generate_code
from jutulgpt.state import GraphState
from jutulgpt.tools import (
    retrieve_jutuldarcy_documentation,
    retrieve_jutuldarcy_examples,
)
from jutulgpt.utils import logger

generate_code_name = "generate_code"
check_code_name = "check_code"
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
# builder.add_node(retrieve_examples_name, ToolNode([retrieve_jutuldarcy_examples]))

# Define tool node for multiple tools
tool_node = ToolNode(
    [
        retrieve_jutuldarcy_documentation,
        retrieve_jutuldarcy_examples,
    ]
)
builder.add_node("tool_node", tool_node)


# # Add edges related to the tools
# builder.add_conditional_edges(
#     START,
#     # Assess LLM decision (call `retriever_tool` tool or respond to the user)
#     tools_condition,
#     {
#         # Translate the condition outputs to nodes in our graph
#         "tools": retrieve_examples_name,
#         END: generate_code_name,
#     },
# )
# # If entered the tool node, continue on to the generate_code
# # builder.add_conditional_edges(
# #     retrieve_examples_name,
# #     generate_code,
# # )
# builder.add_edge("tool_node", generate_code_name)

# From START: decide whether to use tools or go directly to code generation
builder.add_conditional_edges(
    START,
    tools_condition,
    {
        "tools": "tool_node",
        END: generate_code_name,  # if no tools are needed, go to code generation
    },
)

# After tools are run, always go to generate_code
builder.add_edge("tool_node", generate_code_name)


builder.add_edge(START, generate_code_name)
builder.add_edge(generate_code_name, check_code_name)
builder.add_conditional_edges(
    check_code_name,
    decide_to_finish,
    {
        end_name: END,
        # generate_code_name: generate_code_name,
        generate_code_name: generate_code_name,
    },
)
graph = builder.compile()

# Plot the graph
# graph.get_graph().draw_png(output_file_path="./graph.png")
graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
