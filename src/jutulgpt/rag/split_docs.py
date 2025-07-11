import os
import pickle
import re
from abc import ABC
from collections import defaultdict
from typing import Callable, List

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


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
    file_source = doc.metadata.get("source", "Unknown Document")
    return f"## From `{file_source}` - Section: `{section_path}`\n{doc.page_content.strip()}"
