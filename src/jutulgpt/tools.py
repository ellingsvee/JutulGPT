# from langchain.tools.retriever import create_retriever_tool # Dont think this is a good solution since we have to do some additinal processing and fitering.
from langchain_core.tools import tool

from jutulgpt.rag import (
    docs_retriever,
    examples_retriever,
    format_docs,
    format_examples,
)
from jutulgpt.utils import logger

# _docs_retriever_tool = create_retriever_tool(
#     docs_retriever,
#     "retrieve_jutuldarcy_documentation",
#     "Search and return information from the documentation in the JutulDarcy package.",
# )
#
# _examples_retriever_tool = create_retriever_tool(
#     examples_retriever,
#     "retrieve_jutuldarcy_examples",
#     "Search and return Julia code from the JutulDarcy examples.",
# )
#


@tool
def retrieve_jutuldarcy_documentation(query: str) -> str:
    """
    Search and return information from the documentation in the JutulDarcy package.

    Input:
        query: The string sent into the vectorstore retriever.

    Output: String containing the formatted output from the retriever
    """
    logger.info(f"TOOL INVOKED: retrieve_jutuldarcy_documentation")
    out = format_docs(docs_retriever.invoke(input=query))
    print(out)
    return out


@tool
def retrieve_jutuldarcy_examples(query: str) -> str:
    """
    Search and return Julia code from the JutulDarcy examples.

    Input:
        query: The string sent into the vectorstore retriever.

    Output: String containing the formatted output from the retriever
    """
    logger.info("TOOL INVOKED: retrieve_jutuldarcy_examples")
    out = format_examples(examples_retriever.invoke(input=query))
    print(out)
    return out


# tools = [retrieve_jutuldarcy_documentation, retrieve_jutuldarcy_examples]
tools = []  # WARNING: Have inculded the RAG more explicitly instead.
