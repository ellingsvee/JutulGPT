"""This module defines the state graph for the react agent."""

from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from jutulgpt.configuration import MAX_ITERATIONS, AgentConfiguration
from jutulgpt.human_in_the_loop import decide_check_code, response_on_generated_code
from jutulgpt.nodes import check_code, generate_response, tools_node
from jutulgpt.state import State


def decide_to_finish(state: State) -> Literal["generate_response", END]:
    """
    Determines whether to finish.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    error = state.error
    iterations = state.iterations

    if not error or iterations == MAX_ITERATIONS:
        print("decide_to_finish: END")
        return END
    else:
        print("decide_to_finish: generate_response")
        return "generate_response"


builder = StateGraph(State, config_schema=AgentConfiguration)

builder.add_node("generate_response", generate_response)
builder.add_node("tools", tools_node)
builder.add_node("check_code", check_code)
builder.add_node("response_on_generated_code", response_on_generated_code)

builder.add_edge(START, "generate_response")
builder.add_conditional_edges(
    "generate_response",
    tools_condition,
    {
        END: "response_on_generated_code",
        "tools": "tools",
    },
)
builder.add_edge("tools", "generate_response")
builder.add_conditional_edges(
    "response_on_generated_code",
    decide_check_code,
    {
        END: END,
        "check_code": "check_code",
    },
)
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
