"""This module defines the react_tools for agent."""

from jutulgpt.tools import (
    read_from_file_tool,
    retrieve_fimbul_tool,
    retrieve_function_signature_tool,
    retrieve_jutuldarcy_tool,
    write_to_file_tool,
)

agent_tools = [
    retrieve_fimbul_tool,
    retrieve_jutuldarcy_tool,
    retrieve_function_signature_tool,
    read_from_file_tool,
    write_to_file_tool,
]

retrieve_tools = [
    retrieve_fimbul_tool,
    retrieve_jutuldarcy_tool,
    retrieve_function_signature_tool,
]
