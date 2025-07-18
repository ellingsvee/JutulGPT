import os
import pickle
import re
from abc import ABC
from collections import defaultdict
from typing import Callable, List, Tuple, Union

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from jutulgpt.utils import deduplicate_document_chunks


def split_docs(
    document: Document,
) -> List[Document]:
    chunk_size = 500
    chunk_overlap = 50
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ],
        strip_headers=True,
    )
    # text_splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=chunk_size,
    #     chunk_overlap=chunk_overlap,
    # )

    content = document.page_content
    document_metadata = document.metadata.copy()

    splits = markdown_splitter.split_text(content)
    for split in splits:
        split.metadata = {**split.metadata, **document_metadata}

    # splits = text_splitter.split_documents(splits)

    return splits


def format_doc(doc: Document) -> str:
    header_keys = ["Header 1", "Header 2", "Header 3"]
    section_path_parts = [
        str(doc.metadata[k])
        for k in header_keys
        if k in doc.metadata and doc.metadata[k] is not None
    ]
    section_path = " > ".join(section_path_parts) if section_path_parts else "Root"
    return f"{doc.page_content.strip()}"


def get_file_source(doc: Document, for_ui_printing: bool = False) -> str:
    file_source = doc.metadata.get("source", "Unknown Document")
    if for_ui_printing:
        # file_source = os.path.basename(file_source)
        idx = file_source.find("/rag/")
        if idx != -1:
            file_source = file_source[idx + len("/rag/") :]
        return f"{file_source}"
    return file_source


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
        # file_source, section_path = split_docs.get_file_source_and_section_path(doc)
        file_source = get_file_source(doc)
        section_path = get_section_path(doc)
        doc_string += f"# From `{file_source}`\n# Section: `{section_path}`\n"
        doc_string += f"{format_doc(doc)}"
        formatted.append(doc_string)
    return "\n\n".join(formatted)
