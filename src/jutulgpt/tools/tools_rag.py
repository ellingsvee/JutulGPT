from jutulgpt.utils import logger
from jutulgpt.rag import retriever, format_docs


def retrieve_docs(query: str) -> str:
    """Searches JutulDarcy documentation for the given query."""
    logger.info(f"retrieve_docs tool is invoked with query {query}")

    docs = retriever.invoke(query)

    logger.info(f"Info from {len(docs)} were retrieved.")

    context = format_docs(docs)

    # print(f"context: {context}")

    return context
