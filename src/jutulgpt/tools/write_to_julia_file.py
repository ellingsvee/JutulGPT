from typing import Annotated, Any, Optional, cast

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool


@tool(parse_docstring=True)
def write_to_julia_file(
    imports: str,
    code: str,
    filename: str,
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> None:
    """
    Use this tool to write code to a Julia file.

    Args:
        imports: The imports to include at the top of the file.
        code: The code to write to the file.
        filename: The path to the file where the code should be written.

    Returns:
        String containing the path to the written file.
    """

    with open(filename, "w") as f:
        f.write(imports + "\n" + code)
