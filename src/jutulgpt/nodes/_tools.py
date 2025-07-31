"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.tools import (
    ReadFromFile,
    RetrieveFimbulTool,
    RetrieveFunctionSignatureTool,
    RetrieveJutulDarcyTool,
    WriteToFile,
)

tools = [
    RetrieveFimbulTool(),
    RetrieveJutulDarcyTool(),
    RetrieveFunctionSignatureTool(),
    ReadFromFile(),
    WriteToFile(),
]
retrieve_tools = [
    RetrieveFimbulTool(),
    RetrieveJutulDarcyTool(),
    RetrieveFunctionSignatureTool(),
]


tools_node = ToolNode(tools)
