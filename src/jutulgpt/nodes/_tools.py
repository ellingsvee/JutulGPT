"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.tools import retrieve_fimbul, retrieve_jutuldarcy

tools = []

# Add the RAG retrievers as tools
tools.append(retrieve_jutuldarcy)
tools.append(retrieve_fimbul)

tools_node = ToolNode(tools)
