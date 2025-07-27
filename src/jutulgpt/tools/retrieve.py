from typing import Annotated

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

import jutulgpt.rag.retrieval as retrieval
import jutulgpt.rag.split_docs as split_docs
import jutulgpt.rag.split_examples as split_examples
from jutulgpt.configuration import HUMAN_INTERACTION
from jutulgpt.human_in_the_loop import modify_rag_query, response_on_rag
from jutulgpt.rag.retriever_specs import RETRIEVER_SPECS
from jutulgpt.utils import get_file_source

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
    # Modify the query:
    query = modify_rag_query(query=query, retriever_name="JutulDarcy")

    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["jutuldarcy"]["docs"]
    ) as retriever:
        retrieved_docs = retriever.invoke(query)
    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["jutuldarcy"]["examples"]
    ) as retriever:
        retrieved_examples = retriever.invoke(query)

    if HUMAN_INTERACTION:
        retrieved_docs = response_on_rag(
            retrieved_docs,
            get_file_source=get_file_source,
            get_section_path=split_docs.get_section_path,
            format_doc=split_docs.format_doc,
            action_name="Modify retrieved JutulDarcy documentation",
        )
        retrieved_examples = response_on_rag(
            retrieved_examples,
            get_file_source=get_file_source,
            get_section_path=split_examples.get_section_path,
            format_doc=split_examples.format_doc,
            action_name="Modify retrieved JutulDarcy examples",
        )

    docs = split_docs.format_docs(retrieved_docs)
    examples = split_examples.format_examples(retrieved_examples)

    format_str = lambda s: s if s != "" else "(empty)"
    out = f"""
    # Retrieved from the JutulDarcy documentation:

    {format_str(docs)}

    # Retrieved from the JutulDarcy examples:

    {format_str(examples)}
    """

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
    # Modify the query:
    query = modify_rag_query(query=query, retriever_name="Fimbul")

    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["fimbul"]["docs"]
    ) as retriever:
        retrieved_docs = retriever.invoke(query)
    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["fimbul"]["examples"]
    ) as retriever:
        retrieved_examples = retriever.invoke(query)

    print("PRINTING THE RETRIEVED DOCUMENTS:")
    for doc in retrieved_docs:
        print(f"Source: {doc.metadata['source']}")
        print(f"- {doc.page_content[:100]}...\n")

    if HUMAN_INTERACTION:
        retrieved_docs = response_on_rag(
            retrieved_docs,
            get_file_source=get_file_source,
            get_section_path=split_docs.get_section_path,
            format_doc=split_docs.format_doc,
            action_name="Modify retrieved Fimbul documentation",
        )
        retrieved_examples = response_on_rag(
            retrieved_examples,
            get_file_source=get_file_source,
            get_section_path=split_examples.get_section_path,
            format_doc=split_examples.format_doc,
            action_name="Modify retrieved Fimbul examples",
        )

    docs = split_docs.format_docs(retrieved_docs)
    examples = split_examples.format_examples(retrieved_examples)

    print(f"retrieved docs: {docs}")
    print(f"retrieved examples: {examples}")

    format_str = lambda s: s if s != "" else "(empty)"
    out = f"""
    # Retrieved from the Fimbul documentation:

    {format_str(docs)}

    # Retrieved from the Fimbul examples:

    {format_str(examples)}
    """

    return out
