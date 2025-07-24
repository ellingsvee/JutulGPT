import re
from typing import List

from langchain_core.documents import Document


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
