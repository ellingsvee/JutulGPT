import os
import re
from collections import defaultdict
from typing import List

from langchain_core.documents import Document

from jutulgpt.utils import deduplicate_document_chunks


def split_examples(document: Document) -> List[Document]:
    """
    Splits a Document at lines like ``# #` and `# ##`, which represent markdown headings
    inside Julia comments. Keeps all content grouped under each such header.
    Note that we do not split on `# ###` or deeper headings.
    """
    content = document.page_content
    lines = content.splitlines()

    chunks = []
    current_chunk_lines = []
    current_heading = None
    current_metadata = document.metadata.copy()

    def finalize_chunk():
        if current_chunk_lines:
            chunk_text = "\n".join(line for line in current_chunk_lines if line.strip())
            if chunk_text:
                chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata={**current_metadata, "heading": current_heading},
                    )
                )

    for line in lines:
        heading_match = re.match(r"^#\s+(#{1,2})\s+(.*)", line.strip())
        if heading_match:
            # Finalize the previous chunk
            finalize_chunk()
            # Start new chunk
            current_chunk_lines = [line]
            current_heading = heading_match.group(2)
        else:
            current_chunk_lines.append(line)

    # Final chunk
    finalize_chunk()
    return chunks


def get_file_source(doc: Document, for_ui_printing: bool = False) -> str:
    file_source = doc.metadata.get("source", "Unknown Document")
    if for_ui_printing:
        file_source = os.path.basename(file_source)
        # return f"{file_source}"
    return file_source


def get_section_path(doc: Document, for_ui_printing: bool = False) -> str:
    section_path = doc.metadata.get("heading", "No heading")
    if for_ui_printing:
        return section_path
    return section_path


def format_doc(doc: Document) -> str:
    return f"```julia\n{doc.page_content.strip()}\n```"


def format_examples(
    docs: List[Document], n: int = 5, remove_duplicates: bool = True
) -> str:
    if remove_duplicates:
        docs = deduplicate_document_chunks(docs)

    docs = docs[:n]

    grouped = defaultdict(list)
    for doc in docs:
        key = (
            doc.metadata.get("source", "Unknown file"),
            doc.metadata.get("heading", "No heading"),
        )
        grouped[key].append(doc.page_content.strip())

    formatted = []
    for (source, heading), contents in grouped.items():
        section = "\n".join(f"```julia\n{c}\n```" for c in contents)
        formatted.append(f"# From `{source}`\n# Section: `{heading}`\n{section}")
    return "\n\n".join(formatted)
