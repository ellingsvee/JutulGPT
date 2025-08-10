import re
from typing import List

from langchain_core.documents import Document

from jutulgpt.utils import deduplicate_document_chunks, get_file_source


def split_examples(document: Document, header_to_split_on: int = 2) -> List[Document]:
    """
    Splits a Document at lines like `# #`, which represent markdown headings
    inside Julia comments. Keeps all content grouped under each such header.

    For the headers_to_split_on set 1 to split on "# #", 2 to split on "# #" and "# ##", and so on.
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
        heading_match = re.match(
            rf"^#\s+(#{{1,{header_to_split_on}}})\s+(.*)", line.strip()
        )
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


# def get_file_source(doc: Document, for_ui_printing: bool = False) -> str:
#     file_source = doc.metadata.get("source", "Unknown Document")
#     if for_ui_printing:
#         file_source = os.path.basename(file_source)
#     return file_source


def get_section_path(doc: Document, for_ui_printing: bool = False) -> str:
    section_path = doc.metadata.get("heading", "No heading")
    if for_ui_printing:
        return section_path
    return section_path


def format_doc(doc: Document, within_julia_context: bool = True) -> str:
    if within_julia_context:
        return f"```julia\n{doc.page_content.strip()}\n```"
    return doc.page_content.strip()


# TODO: This is currently the exact same code as the format-docs. Should be generalized.
def format_examples(docs: List[Document], remove_duplicates: bool = True) -> str:
    if remove_duplicates:
        docs = deduplicate_document_chunks(docs)

    formatted = []
    for doc in docs:
        example_string = ""
        file_source = get_file_source(doc)
        section_path = get_section_path(doc)
        # section = "\n".join(f"```julia\n{c}\n```" for c in doc.page_content.strip())
        example_string += f"# From `{file_source}`: Section `{section_path}`\n"
        example_string += f"{format_doc(doc, within_julia_context=True)}"
        formatted.append(example_string)

    return "\n\n".join(formatted)
