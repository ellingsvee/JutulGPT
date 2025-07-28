"""This module defines the state graph for the react agent."""

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from jutulgpt.configuration import BaseConfiguration
from jutulgpt.nodes import check_code, generate_response, tools_node
from jutulgpt.state import State


def decide_to_finish(
    state: State, config: RunnableConfig
) -> Literal["generate_response", END]:
    """
    Determines whether to finish.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    error = state.error
    iterations = state.iterations

    configuration = BaseConfiguration.from_runnable_config(config)

    if not error or iterations == configuration.max_iterations:
        print("decide_to_finish: END")
        return END
    else:
        print("decide_to_finish: generate_response")
        return "generate_response"


builder = StateGraph(State, config_schema=BaseConfiguration)

builder.add_node("generate_response", generate_response)
builder.add_node("tools", tools_node)
builder.add_node("check_code", check_code)

builder.add_edge(START, "generate_response")
builder.add_conditional_edges(
    "generate_response",
    tools_condition,
    {
        END: "check_code",
        "tools": "tools",
    },
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
