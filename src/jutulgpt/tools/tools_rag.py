from jutulgpt.utils import logger
from jutulgpt.rag import docs_retriever, format_docs
from langchain.tools.retriever import create_retriever_tool


# def retrieve_docs(query: str) -> str:
#     """Searches JutulDarcy documentation for the given query."""
#     logger.info(f"retrieve_docs tool is invoked with query {query}")
#
#     docs = retriever.invoke(query)
#
#     logger.info(f"Info from {len(docs)} were retrieved.")
#
#     context = format_docs(docs)
#
#     # print(f"context: {context}")
#
#     return context


docs_retriever_tool = create_retriever_tool(
    docs_retriever,
    "retrieve_jutuldarcy_documentation",
    "Search and return information in the Documentation of the JutulDarcy package.",
)
