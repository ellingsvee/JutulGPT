from typing import Annotated, Any, Callable, List, Optional, cast

from dotenv import find_dotenv, load_dotenv
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import Command, interrupt

# from jutulgpt.rag.split_docs import (
#     format_doc,
#     format_docs,
#     get_file_source,
#     get_section_path,
#     modify_doc_content,
# )
import jutulgpt.rag.split_docs as split_docs
import jutulgpt.rag.split_examples as split_examples
from jutulgpt.configuration import Configuration
from jutulgpt.rag.retrievers import retrievers
from jutulgpt.rag.utils import modify_doc_content

_: bool = load_dotenv(find_dotenv())


def get_human_response_on_rag(
    docs: List[Document],
    get_file_source: Callable,
    get_section_path: Callable,
    format_doc: Callable,
    action_name: str = "Modify",
):
    if not docs:
        return docs

    # TODO: Handle the case when the get_section_path retrieved the same section path for multiple documents
    action_request_args = {}
    arg_names = []
    for _, doc in enumerate(docs):
        section_path = get_section_path(doc, for_ui_printing=True)
        file_source = get_file_source(doc, for_ui_printing=True)
        arg_name = f"{file_source} - {section_path}"
        # arg_name = section_path
        arg_names.append(arg_name)
        action_request_args[f"{arg_name}"] = format_doc(doc)

    description = "The RAG provided you with the following documents. You can modify the content of any of these documents by editing the text in the input boxes below. If you do not want to modify a document, leave the input box empty."
    request = HumanInterrupt(
        action_request=ActionRequest(
            action=action_name,
            args=action_request_args,
        ),
        config=HumanInterruptConfig(
            allow_ignore=True,
            allow_accept=False,
            allow_respond=False,
            allow_edit=True,
        ),
        description=description,
    )

    human_response: HumanResponse = interrupt([request])[0]
    response_type = human_response.get("type")
    if response_type == "edit":
        args_dics = human_response.get("args", {}).get("args", {})
        for arg_name, new_content in args_dics.items():
            if not new_content:
                # Remove the document if new_content is empty
                docs.pop(arg_names.index(arg_name))
                arg_names.pop(arg_names.index(arg_name))
                continue
            doc = docs[arg_names.index(arg_name)]
            docs[arg_names.index(arg_name)] = modify_doc_content(doc, new_content)

    elif response_type == "ignore":
        pass
    else:
        raise TypeError(f"Interrupt value of type {response_type} is not supported.")

    return docs


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

    retrieved_docs = get_human_response_on_rag(
        retrieved_docs,
        get_file_source=split_docs.get_file_source,
        get_section_path=split_docs.get_section_path,
        format_doc=split_docs.format_doc,
        action_name="Modify retrieved documentation",
    )
    retrieved_examples = get_human_response_on_rag(
        retrieved_examples,
        get_file_source=split_examples.get_file_source,
        get_section_path=split_examples.get_section_path,
        format_doc=split_examples.format_doc,
        action_name="Modify retrieved examples",
    )

    print("Retrieved documents:", retrieved_docs)  # WARNING: DELETE LATER
    print("Retrieved examples:", retrieved_examples)  # WARNING: DELETE LATER

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

    configuration = Configuration.from_runnable_config(config)  # Temp

    print("TOOL INVOKED: retrieve_fimbul")

    retrieved_docs = retrievers["fimbul"]["docs"].invoke(input=query)
    retrieved_examples = retrievers["fimbul"]["examples"].invoke(input=query)

    docs = format_docs(retrieved_docs)
    examples = format_examples(retrieved_examples)

    #     out = f"""
    # # Retrieved from the Fimbul documentation:
    # {docs}

    # # Retrieved from the Fimbul examples:
    # {examples}
    # """
    out = f"""
    # Retrieved from the Fimbul documentation
    <details>
    <summary>Show documentation</summary>

    {docs}

    </details>

    # Retrieved from the Fimbul examples
    <details>
    <summary>Show examples</summary>

    {examples}

    </details>
    """
    print(out)  # WARNING: DELETE LATER

    return out
