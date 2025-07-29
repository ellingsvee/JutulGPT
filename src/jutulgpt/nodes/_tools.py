"""This module defines the react_tools for agent."""

from langgraph.prebuilt import ToolNode

from jutulgpt.tools import RetrieveFimbulTool, RetrieveJutulDarcyTool

tools = [RetrieveFimbulTool(), RetrieveJutulDarcyTool()]

# Add the RAG retrievers as tools
# tools.append(retrieve_jutuldarcy)
# tools.append(retrieve_fimbul)

tools_node = ToolNode(tools)
