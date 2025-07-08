# from langchain.tools.retriever import create_retriever_tool # Dont think this is a good solution since we have to do some additinal processing and fitering.
from langchain_core.tools import tool
from langgraph.types import interrupt

from jutulgpt.rag import (
    docs_retriever,
    examples_retriever,
    format_docs,
    format_examples,
)
from jutulgpt.utils import logger


@tool(response_format="content_and_artifact")
def retrieve_jutuldarcy(query: str):
    """
    Use this tool to look up any information, usage, or examples from the JutulDarcy documentation. ALWAYS use this tool before answering any Julia code question about JutulDarcy.

    Input:
        query: The string sent into the vectorstore retriever.

    Output: String containing the formatted output from the retriever
    """
    logger.info(f"Tool invoked: retrieve_jutuldarcy with query: {query}")

    retrieved_docs = docs_retriever.invoke(input=query)
    retrieved_examples = examples_retriever.invoke(input=query)
    retrieved = retrieved_docs + retrieved_examples

    docs = format_docs(retrieved_docs)
    examples = format_examples(retrieved_examples)

    out = f"""
# Retrieved from the JutulDarcy documentation:
{docs}

# Retrieved from the JutulDarcy examples:
{examples}
"""

    # print(out)

    return out, retrieved


@tool(parse_docstring=True)
def write_code_to_julia_file(imports: str, code: str, filename: str):
    """
    Use this tool to write code to a Julia file.

    Args:
        imports: The imports to include at the top of the file.
        code: The code to write to the file.
        filename: The path to the file where the code should be written.

    Returns:
        String containing the path to the written file.
    """

    logger.info(f"Tool invoked: write_code_to_julia_file")

    #    filename = interrupt("Provide filepath to where you want to save the file:")

    with open(filename, "w") as f:
        f.write(imports + "\n" + code)

    return f"Code written to {filename}"


tools = [retrieve_jutuldarcy, write_code_to_julia_file]
