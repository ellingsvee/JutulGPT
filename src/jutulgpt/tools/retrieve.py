from typing import Annotated

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from langgraph.types import interrupt

import jutulgpt.rag.split_docs as split_docs
import jutulgpt.rag.split_examples as split_examples
from jutulgpt.configuration import Configuration
from jutulgpt.human_in_the_loop.response_on_rag import response_on_rag
from jutulgpt.rag.retrievers import retrievers
from jutulgpt.rag.utils import modify_doc_content

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
    print("TOOL INVOKED: retrieve_jutuldarcy")

    retrieved_docs = retrievers["jutuldarcy"]["docs"].invoke(input=query)
    retrieved_examples = retrievers["jutuldarcy"]["examples"].invoke(input=query)

    retrieved_docs = response_on_rag(
        retrieved_docs,
        get_file_source=split_docs.get_file_source,
        get_section_path=split_docs.get_section_path,
        format_doc=split_docs.format_doc,
        action_name="Modify retrieved documentation",
    )
    retrieved_examples = response_on_rag(
        retrieved_examples,
        get_file_source=split_examples.get_file_source,
        get_section_path=split_examples.get_section_path,
        format_doc=split_examples.format_doc,
        action_name="Modify retrieved examples",
    )

    docs = split_docs.format_docs(retrieved_docs)
    examples = split_examples.format_examples(retrieved_examples)

    print("Creating output")  # WARNING: DELETE LATER
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
    print("TOOL INVOKED: retrieve_fimbul")

    retrieved_docs = retrievers["fimbul"]["docs"].invoke(input=query)
    retrieved_examples = retrievers["fimbul"]["examples"].invoke(input=query)

    retrieved_docs = response_on_rag(
        retrieved_docs,
        get_file_source=split_docs.get_file_source,
        get_section_path=split_docs.get_section_path,
        format_doc=split_docs.format_doc,
        action_name="Modify retrieved documentation",
    )
    retrieved_examples = response_on_rag(
        retrieved_examples,
        get_file_source=split_examples.get_file_source,
        get_section_path=split_examples.get_section_path,
        format_doc=split_examples.format_doc,
        action_name="Modify retrieved examples",
    )

    docs = split_docs.format_docs(retrieved_docs)
    examples = split_examples.format_examples(retrieved_examples)

    out = f"""
    # Retrieved from the Fimbul documentation:

    {docs}

    # Retrieved from the Fimbul examples:

    {examples}
    """
    print(out)  # WARNING: DELETE LATER

    return out
