"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.tools import (
    ReadFromFile,
    RetrieveFimbulTool,
    RetrieveJutulDarcyTool,
    WriteToFile,
)

tools = [RetrieveFimbulTool(), RetrieveJutulDarcyTool(), ReadFromFile(), WriteToFile()]
retrieve_tools = [RetrieveFimbulTool(), RetrieveJutulDarcyTool()]


tools_node = ToolNode(tools)
