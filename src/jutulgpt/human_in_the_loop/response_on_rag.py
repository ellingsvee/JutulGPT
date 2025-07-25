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
    Presents retrieved RAG documents to the user for optional modification before sending them as LLM context.

    This function enables a human-in-the-loop workflow, allowing the user to review and edit the content of each document.
    If the user deletes all content for a document, that document is removed from the list. The function supports custom
    formatting and section/file labeling for each document.

    Args:
        docs (List[Document]): List of documents retrieved by the RAG system.
        get_file_source (Callable): Function to get the file source of a document (for UI display).
        get_section_path (Callable): Function to get the section path of a document (for UI display).
        format_doc (Callable): Function to format a document for display in the UI.
        action_name (str, optional): Name of the action to be displayed in the UI. Defaults to "Modify".

    Returns:
        List[Document]: The list of documents after potential modifications by the user. Documents with empty content are removed.
    """
    if not docs:
        return docs  # Nothing to do if no documents

    action_request_args = {}
    arg_names = []

    # Build the arguments for the UI, ensuring unique names for each document
    for _, doc in enumerate(docs):
        section_path = get_section_path(doc)
        file_source = get_file_source(doc)
        arg_name = f"{file_source} - {section_path}"
        # Ensure arg_name is unique by appending a suffix if needed
        original_arg_name = arg_name
        suffix = 1
        while arg_name in action_request_args:
            arg_name = f"{original_arg_name} ({suffix}kh"
            suffix += 1
        arg_names.append(arg_name)
        content = format_doc(doc)
        action_request_args[arg_name] = content

    # Prepare the human-in-the-loop UI request
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

    # Wait for the user's response from the UI
    human_response: HumanResponse = interrupt([request])[0]
    response_type = human_response.get("type")
    if response_type == "edit":
        # User edited one or more documents
        args_dics = human_response.get("args", {}).get("args", {})
        for arg_name, new_content in args_dics.items():
            if not new_content:
                # Remove the document if new_content is empty
                docs.pop(arg_names.index(arg_name))
                arg_names.pop(arg_names.index(arg_name))
                continue
            # Update the document with the new content
            doc = docs[arg_names.index(arg_name)]
            docs[arg_names.index(arg_name)] = modify_doc_content(doc, new_content)

    elif response_type == "ignore":
        # User chose to ignore editing
        pass
    else:
        # Unexpected response type
        raise TypeError(f"Interrupt value of type {response_type} is not supported.")

    return docs
