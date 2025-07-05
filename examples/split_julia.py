# src/jutulgpt/rag_sources/jutuldarcy_examples/introduction/wells_intro.jl


# 1. Define the path to your Julia code file
julia_file_path = (
    "./src/jutulgpt/rag_sources/jutuldarcy_examples/introduction/wells_intro.jl"
)
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from typing import List

import re
from langchain_core.documents import Document
from typing import List


def split_on_julia_markdown_headers(document: Document) -> List[Document]:
    """
    Splits a Document at lines like `# ##` or `# ###`, which represent markdown headings
    inside Julia comments. Keeps all content grouped under each such header.
    """
    content = document.page_content
    lines = content.splitlines()

    chunks = []
    current_chunk_lines = []
    current_heading = None
    current_metadata = document.metadata.copy()

    def finalize_chunk():
        if current_chunk_lines:
            chunk_text = "\n".join(current_chunk_lines).strip()
            if chunk_text:
                chunks.append(
                    Document(
                        page_content=chunk_text,
                        metadata={**current_metadata, "heading": current_heading},
                    )
                )

    for line in lines:
        heading_match = re.match(r"^#\s+(#{1,6})\s+(.*)", line.strip())
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


class JuliaCodeLoader(BaseLoader):
    """Loads Julia (.jl) files and creates LangChain Documents."""

    def __init__(self, file_path: str):
        self.file_path = file_path

    def load(self) -> List[Document]:
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
        metadata = {"source": os.path.basename(self.file_path)}
        return [Document(page_content=content, metadata=metadata)]


class JuliaCodeSplitter(RecursiveCharacterTextSplitter):
    """
    Splits Julia files with awareness of comment blocks and function boundaries.
    """

    def __init__(self, chunk_size=1000, chunk_overlap=100):
        super().__init__(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "# ", "\n", " "],
        )


# Example usage:
def load_and_split_julia_code(path_to_file):
    loader = JuliaCodeLoader(path_to_file)
    docs = loader.load()

    # splitter = JuliaCodeSplitter(chunk_size=1000, chunk_overlap=100)
    # chunks = splitter.split_documents(docs)

    # Apply heading-aware splitting
    chunks = []
    for doc in docs:
        chunks.extend(split_on_julia_markdown_headers(doc))

    return chunks


# --- For testing ---
if __name__ == "__main__":
    from pprint import pprint

    chunks = load_and_split_julia_code(julia_file_path)  # Replace with your file path
    for i, chunk in enumerate(chunks):
        print(f"\n--- Chunk {i + 1} ---")
        print(chunk.page_content)
