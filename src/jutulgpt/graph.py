from dataclasses import dataclass
from typing import Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tool_node, tools_condition
from ollama import Tool

from jutulgpt.agents import memory
from jutulgpt.config import avoid_tools, max_iterations
from jutulgpt.nodes import check_code, generate_code, retrieve_context, start_node
from jutulgpt.state import Code, GraphState, InputState
from jutulgpt.tools import retrieve_jutuldarcy, write_code_to_julia_file
from jutulgpt.utils import logger

start_node_name = "start_node"
generate_code_name = "generate_code"
retrieve_context_name = "retrieve_context"
check_code_name = "check_code"
start_name = "start"
end_name = "end"


def decide_to_finish(state: GraphState):
    if not state.error or state.iterations == max_iterations:
        logger.info("Decision: Finish")
        if state.iterations == max_iterations:
            print(f"Max iterations {max_iterations} reached.")
        return end_name
    logger.info("Decision: Retry")
    return generate_code_name


def build_graph(avoid_tools=False):
    builder = StateGraph(GraphState, input_schema=InputState)

    builder.add_node(start_node_name, start_node)
    builder.add_node(generate_code_name, generate_code)
    builder.add_node(check_code_name, check_code)

    # tools = ToolNode([retrieve_jutuldarcy])
    tools = ToolNode([retrieve_jutuldarcy, write_code_to_julia_file])

    if not avoid_tools:
        builder.add_node(tools)

    builder.set_entry_point(start_node_name)

    if avoid_tools:
        # Go via the retrieve_context node to retrieve context explicitly
        builder.add_node(retrieve_context_name, retrieve_context)
        builder.add_edge(start_node_name, retrieve_context_name)
        builder.add_edge(retrieve_context_name, generate_code_name)
    else:
        builder.add_edge(start_node_name, generate_code_name)

    if avoid_tools:
        # If avoid_tools is True, we do not use the tools node
        builder.add_edge(generate_code_name, check_code_name)
    else:
        builder.add_conditional_edges(
            generate_code_name,
            tools_condition,
            {END: check_code_name, "tools": "tools"},
        )
        builder.add_edge("tools", check_code_name)
    # builder.add_edge(generate_code_name, END)
    builder.add_conditional_edges(
        check_code_name,
        decide_to_finish,
        {
            end_name: END,
            generate_code_name: generate_code_name,
        },
    )

    # graph = builder.compile(checkpointer=memory)
    return builder.compile(name="JutulGPTGraph")


# Generate and plot the graph
graph = build_graph(avoid_tools=avoid_tools)
graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
