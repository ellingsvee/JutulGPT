from typing import Annotated, Any, List, Optional, cast

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from jutulgpt.julia_interface import run_string


@tool(parse_docstring=True)
def docstring_extractor(
    function_names: List[str],
    *,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> List[str]:
    """
    This tool extracts the docstrings of specified Julia functions from the Jutul, JutulDarcy, and Fimbul packages.

    Args:
        function_names: A list of function names for which to extract docstrings.

    Returns:
        A list of docstrings corresponding to the provided function names.
    """

    docstring_list = []
    for function_name in function_names:
        result = run_string(f"@doc {function_name}")
        if result["error"]:
            docstring_list.append(f"Could not retrieve docstring for {function_name}")
        else:
            docstring_list.append(str(result["out"]))

    return docstring_list
