from typing import Annotated, Any, Optional, cast

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool


@tool(parse_docstring=True)
def read_from_file(
    filename: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """
    Use this tool read the content of a file.
    Note, the tool only accept reading files with the following extensions: .jl, .txt, .md, .json, .yaml, .yml.

    Args:
        filename: The path to the file you want to read.

    Output:
        The content of the file as a string.
    """

    if not filename.endswith((".jl", ".txt", ".md", ".json", ".yaml", ".yml")):
        # raise ValueError("Unsupported file extension. Supported extensions are: .jl, .txt, .md, .json, .yaml, .yml")
        return "Unsupported file extension. Supported extensions are: .jl, .txt, .md, .json, .yaml, .yml"

    load_dotenv(find_dotenv())
    with open(filename, "r") as file:
        content = file.read()

    # Return the content of the file
    return cast(str, content)
