"""This module defines the state graph for the react agent."""

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from jutulgpt.configuration import Configuration, max_iterations
from jutulgpt.nodes import check_code, generate_response, tools_node
from jutulgpt.state import State

# def decide_to_finish(state: State):
#     if not state.error or state.iterations == max_iterations:
#         if state.iterations == max_iterations:
#             # print(f"Max iterations {max_iterations} reached.")
#         return END
#     return "generate_response"


def decide_to_finish(state: State):
    """
    Determines whether to finish.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    error = state.error
    iterations = state.iterations

    if not error or iterations == max_iterations:
        return END
    else:
        return "generate_response"


builder = StateGraph(State, config_schema=Configuration)

builder.add_node("generate_response", generate_response)
builder.add_node("tools", tools_node)
builder.add_node("check_code", check_code)

builder.add_edge(START, "generate_response")
builder.add_conditional_edges(
    "generate_response",
    tools_condition,
    {END: "check_code", "tools": "tools"},
)
builder.add_edge("tools", "generate_response")

builder.add_conditional_edges(
    "check_code",
    decide_to_finish,
    {
        END: END,
        "generate_response": "generate_response",
    },
)


graph = builder.compile(name="agent")

graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
