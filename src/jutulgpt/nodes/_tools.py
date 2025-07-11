"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.configuration import retrieve_fimbul, retrieve_jutuldacy
from jutulgpt.tools import (
    read_from_file,
    retrieve_fimbul,
    retrieve_jutuldarcy,
    write_to_file,
)

tools = [write_to_file, read_from_file]

if retrieve_jutuldacy:
    tools.append(retrieve_jutuldarcy)
if retrieve_fimbul:
    tools.append(retrieve_fimbul)

tools_node = ToolNode(tools)
