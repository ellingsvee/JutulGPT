from typing import Annotated, Any, Optional, cast

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

from jutulgpt.configuration import Configuration
from jutulgpt.rag import (
    docs_retriever,
    examples_retriever,
    format_docs,
    format_examples,
)

_: bool = load_dotenv(find_dotenv())


@tool(parse_docstring=True)
def retrieve(query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]) -> str:
    """
    Use this tool to look up any information, usage, or examples from the JutulDarcy documentation. ALWAYS use this tool before answering any Julia code question about JutulDarcy.

    Args:
        query: The string sent into the vectorstore retriever.

    Returns:
        String containing the formatted output from the retriever
    """

    configuration = Configuration.from_runnable_config(config)  # Temp

    print("TOOL INVOKED: retrieve")

    retrieved_docs = docs_retriever.invoke(input=query)
    retrieved_examples = examples_retriever.invoke(input=query)
    # retrieved = retrieved_docs + retrieved_examples

    docs = format_docs(retrieved_docs)
    examples = format_examples(retrieved_examples)

    out = f"""
# Retrieved from the JutulDarcy documentation:
{docs}

# Retrieved from the JutulDarcy examples:
{examples}
"""

    return out
