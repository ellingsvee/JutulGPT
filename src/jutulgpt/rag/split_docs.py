import re
from typing import List

from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
)

from jutulgpt.utils import deduplicate_document_chunks, get_file_source


def split_docs(
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

    # Make the page content more readable
    page_content = remove_markdown_links(page_content)

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

        # Easy workaround for the duplications of the headers
        # Caused by the markdown splitter making header become "MyHeader {# MyHeader}"
        section_path = re.sub(r"\s*\{[^}]*\}", "", section_path)
        return section_path
    section_path = " > ".join(section_path_parts) if section_path_parts else "Root"
    return section_path


def format_docs(docs, n: int = 5, remove_duplicates: bool = True):
    if remove_duplicates:
        docs = deduplicate_document_chunks(docs)
    docs = docs[:n]

    formatted = []
    for doc in docs:
        doc_string = ""
        file_source = get_file_source(doc)
        section_path = get_section_path(doc)
        doc_string += f"# From `{file_source}`\n# Section: `{section_path}`\n"
        doc_string += f"{format_doc(doc)}"
        formatted.append(doc_string)
    return "\n\n".join(formatted)
