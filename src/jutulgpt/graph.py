from dataclasses import dataclass
from typing import Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tool_node, tools_condition
from ollama import Tool

from jutulgpt.agents import memory
from jutulgpt.config import max_iterations
from jutulgpt.nodes import check_code, generate_code, start_node
from jutulgpt.state import Code, GraphState, InputState
from jutulgpt.tools import retrieve_jutuldarcy, write_code_to_julia_file
from jutulgpt.utils import logger

start_node_name = "start_node"
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


graph_builder = StateGraph(GraphState, input_schema=InputState)

graph_builder.add_node(start_node_name, start_node)
graph_builder.add_node(generate_code_name, generate_code)
graph_builder.add_node(check_code_name, check_code)

# tools = ToolNode([retrieve_jutuldarcy])
tools = ToolNode([retrieve_jutuldarcy, write_code_to_julia_file])
graph_builder.add_node(tools)


graph_builder.set_entry_point(start_node_name)
graph_builder.add_edge(start_node_name, generate_code_name)

graph_builder.add_conditional_edges(
    generate_code_name,
    tools_condition,
    {END: check_code_name, "tools": "tools"},
)
graph_builder.add_edge("tools", check_code_name)
graph_builder.add_edge(generate_code_name, END)
graph_builder.add_conditional_edges(
    check_code_name,
    decide_to_finish,
    {
        end_name: END,
        generate_code_name: generate_code_name,
    },
)

# graph = graph_builder.compile(checkpointer=memory)
graph = graph_builder.compile(name="JutulGPTGraph")

# Plot the graph
graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
