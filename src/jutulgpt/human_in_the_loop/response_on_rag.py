from typing import Callable, List

from langchain_core.documents import Document
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt

from jutulgpt.rag.utils import modify_doc_content


def response_on_rag(
    docs: List[Document],
    get_file_source: Callable,
    get_section_path: Callable,
    format_doc: Callable,
    action_name: str = "Modify",
):
    """
    Human in the loop. The user can modify the retrieved documents before it is sent as context to the LLM.
    Deleting all content in the input box for a document will remove that document from the list of documents.

    Args:
        docs: List of documents retrieved by the RAG system.
        get_file_source: Function to get the file source of a document.
        get_section_path: Function to get the section path of a document.
        format_doc: Function to format a document for display.
        action_name: Name of the action to be displayed in the UI.
    Returns:
        List of documents after potential modifications by the user.
    """
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
