"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.configuration import RETRIEVE_FIMBUL
from jutulgpt.tools import (
    read_from_file,
    retrieve_fimbul,
    retrieve_jutuldarcy,
    write_to_file,
)

tools = [write_to_file, read_from_file]

# Add the RAG retrievers as tools
tools.append(retrieve_jutuldarcy)
if RETRIEVE_FIMBUL:
    tools.append(retrieve_fimbul)

tools_node = ToolNode(tools)
