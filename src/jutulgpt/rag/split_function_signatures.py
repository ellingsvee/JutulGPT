import re
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

from jutulgpt.utils import deduplicate_document_chunks


def split_function_signatures(
    document: Document,
) -> List[Document]:
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ],
        strip_headers=True,
    )
    content = document.page_content
    document_metadata = document.metadata.copy()

    splits = markdown_splitter.split_text(content)
    for split in splits:
        split.metadata = {**split.metadata, **document_metadata}

    return splits


def remove_markdown_links(text: str) -> str:
    # Replace [text](url) with just text
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)


def format_doc(doc: Document) -> str:
    page_content = doc.page_content.strip()
    return f"{page_content}"


def get_section_path(doc: Document, for_ui_printing: bool = False) -> str:
    header_keys = ["Header 1", "Header 2", "Header 3"]
    section_path_parts = [
        str(doc.metadata[k])
        for k in header_keys
        if k in doc.metadata and doc.metadata[k] is not None
    ]

    if for_ui_printing:
        section_path = section_path_parts[0] if section_path_parts else "Root"
        return section_path
    section_path = " > ".join(section_path_parts) if section_path_parts else "Root"
    return section_path


def format_docs(docs, remove_duplicates: bool = True):
    if remove_duplicates:
        docs = deduplicate_document_chunks(docs)

    formatted = []
    for doc in docs:
        doc_string = ""
        function_name = doc.metadata.get("Header 3", "Unknown Function")
        function_signature = format_doc(doc)
        if function_signature:
            doc_string += f"# Function: {function_name}\n"
            doc_string += f"{function_signature}"

        formatted.append(doc_string)
    return "\n\n---\n\n".join(formatted)


def find_function_docs_by_names(
    docs: List[Document], function_names: List[str]
) -> tuple[List[Document], List[str]]:
    """
    Find documents that match the given function names.

    Args:
        docs: List of documents to search through
        function_names: List of function names to find

    Returns:
        Tuple of (found_documents, missing_function_names)
    """
    # Create a mapping from function names to documents
    function_docs = {}
    for doc in docs:
        func_name = doc.metadata.get("Header 3")
        if func_name:
            # Store both exact name and cleaned name for better matching
            function_docs[func_name] = doc
            # Also store a cleaned version (remove special characters, lowercase)
            cleaned_name = re.sub(r"[^\w]", "", func_name.lower())
            function_docs[cleaned_name] = doc

    # Find matching documents
    found_docs = []
    missing_functions = []

    for func_name in function_names:
        found = False

        # Try exact match first
        if func_name in function_docs:
            found_docs.append(function_docs[func_name])
            found = True
        else:
            # Try cleaned match
            cleaned_search = re.sub(r"[^\w]", "", func_name.lower())
            if cleaned_search in function_docs:
                found_docs.append(function_docs[cleaned_search])
                found = True

        if not found:
            missing_functions.append(func_name)

    # Remove duplicates while preserving order
    seen = set()
    unique_found_docs = []
    for doc in found_docs:
        doc_id = id(doc)  # Use object id to identify unique documents
        if doc_id not in seen:
            seen.add(doc_id)
            unique_found_docs.append(doc)

    return unique_found_docs, missing_functions
