from typing import Annotated

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool

import jutulgpt.rag.retrieval as retrieval
import jutulgpt.rag.split_docs as split_docs
import jutulgpt.rag.split_examples as split_examples
from jutulgpt.configuration import BaseConfiguration, INTERACTIVE_ENVIRONMENT
from jutulgpt.human_in_the_loop.response_on_rag import response_on_rag
from jutulgpt.rag.retriever_specs import RETRIEVER_SPECS

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
    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["jutuldarcy"]["docs"]
    ) as retriever:
        retrieved_docs = retriever.invoke(query)
    with retrieval.make_retriever(
        config=config, spec=RETRIEVER_SPECS["jutuldarcy"]["examples"]
    ) as retriever:
        retrieved_examples = retriever.invoke(query)

    configuration = BaseConfiguration.from_runnable_config(config)

    if INTERACTIVE_ENVIRONMENT:
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
    # Retrieved from the JutulDarcy documentation:

    {docs}

    # Retrieved from the JutulDarcy examples:

    {examples}
    """

    return out


# @tool(parse_docstring=True)
# TODO: RE-Implement
def retrieve_fimbul(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """
    Temporary not implemented
    """
    raise NotImplementedError(
        "The Fimbul retrieval tool is not implemented yet. Please check back later."
    )
