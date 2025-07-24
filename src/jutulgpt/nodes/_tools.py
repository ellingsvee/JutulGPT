"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.tools import (
    read_from_file,
    retrieve_jutuldarcy,
    write_to_file,
)

tools = [write_to_file, read_from_file]

tools.append(retrieve_jutuldarcy)
# tools.append(retrieve_fimbul) # WARNING: Removed for the time being. Need to find out how to best structure this.

tools_node = ToolNode(tools)
