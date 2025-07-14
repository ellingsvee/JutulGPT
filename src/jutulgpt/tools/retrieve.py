from typing import Annotated, Any, Optional, cast

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from jutulgpt.configuration import Configuration
from jutulgpt.rag.retrievers import (
    format_docs,
    format_examples,
    retrievers,
)

_: bool = load_dotenv(find_dotenv())


@tool(parse_docstring=True)
def retrieve_jutuldarcy(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Use this tool to look up any information, usage, or examples from the JutulDarcy documentation. ALWAYS use this tool before answering any Julia code question about JutulDarcy.

    Args:
        query: The string sent into the vectorstore retriever.

    Returns:
        String containing the formatted output from the retriever
    """

    configuration = Configuration.from_runnable_config(config)  # Temp

    print("TOOL INVOKED: retrieve_jutuldarcy")

    retrieved_docs = retrievers["jutuldarcy"]["docs"].invoke(input=query)
    retrieved_examples = retrievers["jutuldarcy"]["examples"].invoke(input=query)
    # retrieved = retrieved_docs + retrieved_examples

    docs = format_docs(retrieved_docs)
    examples = format_examples(retrieved_examples)

    out = f"""
# Retrieved from the JutulDarcy documentation:
{docs}

# Retrieved from the JutulDarcy examples:
{examples}
"""

    print(out)  # WARNING: DELETE LATER

    return out


@tool(parse_docstring=True)
def retrieve_fimbul(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Use this tool to look up any information, usage, or examples from the Fimbul documentation. ALWAYS use this tool before answering any Julia code question about Fimbul.

    Args:
        query: The string sent into the vectorstore retriever.

    Returns:
        String containing the formatted output from the retriever
    """

    configuration = Configuration.from_runnable_config(config)  # Temp

    print("TOOL INVOKED: retrieve_fimbul")

    retrieved_docs = retrievers["fimbul"]["docs"].invoke(input=query)
    retrieved_examples = retrievers["fimbul"]["examples"].invoke(input=query)

    docs = format_docs(retrieved_docs)
    examples = format_examples(retrieved_examples)

    out = f"""
# Retrieved from the Fimbul documentation:
{docs}

# Retrieved from the Fimbul examples:
{examples}
"""
    print(out)  # WARNING: DELETE LATER

    return out
