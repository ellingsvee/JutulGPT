"""This module defines the state graph for the react agent."""

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from jutulgpt.configuration import Configuration
from jutulgpt.nodes import generate_response, tools_node
from jutulgpt.state import State

builder = StateGraph(State, config_schema=Configuration)

builder.add_node("generate_response", generate_response)
builder.add_node("tools", tools_node)

builder.add_edge(START, "generate_response")
builder.add_conditional_edges("generate_response", tools_condition, ["tools", END])
builder.add_edge("tools", "generate_response")

graph = builder.compile()

graph.name = "agent"
