"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.tools import retrieve, write_to_julia_file

tools = [retrieve, write_to_julia_file]
tools_node = ToolNode(tools)
