import os
import pickle
import re

# persist_directory = "./chroma_docs_dir"
# loaded_docs_path = "./src/jutulgpt/rag_sources/loaded_docs.pkl"
# if os.path.exists(loaded_docs_path):
#     logger.info("Loading existing loaded_docs from disk.")
#     with open(loaded_docs_path, "rb") as f:
#         loaded = pickle.load(f)
# else:
#     logger.info("loaded_docs not found. Generating new one.")
#     loader_docs = DirectoryLoader(
#         path="./src/jutulgpt/rag_sources/jutuldarcy_docs/man/",
#         glob="**/*.md",
#         show_progress=True,
#         loader_cls=UnstructuredMarkdownLoader,
#     )
#
#     loaded = loader_docs.load()
#
#     with open(loaded_docs_path, "wb") as f:
#         pickle.dump(loaded, f)
#
# splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
# splits = splitter.split_documents(loaded)
#
# vectorstore = Chroma.from_documents(
#     documents=splits,
#     embedding=embedding,
#     persist_directory=persist_directory,
# )
#
# docs_retriever = vectorstore.as_retriever()
# def format_docs(docs):
#     return "\n\n".join(doc.page_content for doc in docs)
from collections import defaultdict
from typing import AsyncIterator, Iterator, List

from langchain.text_splitter import TextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredFileLoader,
    UnstructuredMarkdownLoader,
)
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_core.core_schema import lax_or_strict_schema

from jutulgpt.config import embedding
from jutulgpt.utils import logger


def format_docs(docs: List[Document]) -> str:
    formatted_chunks = []
    for doc in docs:
        heading = doc.metadata.get("heading", "No heading")
        source = doc.metadata.get("source", "Unknown file")
        formatted_chunks.append(
            f"### From `{source}` — Section: `{heading}`\n\n{doc.page_content.strip()}"
        )
    return "\n\n---\n\n".join(formatted_chunks)


def format_docs_grouped_by_source(docs: List[Document]) -> str:
    grouped = defaultdict(list)
    for doc in docs:
        key = (
            doc.metadata.get("source", "Unknown file"),
            doc.metadata.get("heading", "No heading"),
        )
        grouped[key].append(doc.page_content.strip())

    formatted = []
    for (source, heading), contents in grouped.items():
        section = "\n".join(contents)
        formatted.append(f"### From `{source}` — Section: `{heading}`\n\n{section}")
    return "\n\n---\n\n".join(formatted)


def split_julia_file_on_markdown_headers(document: Document) -> List[Document]:
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


def load_and_split_julia_code(path_to_file: str) -> List[Document]:
    loader = JuliaCodeLoader(path_to_file)
    docs = loader.load()

    # Apply heading-aware splitting
    chunks = []
    for doc in docs:
        chunks.extend(split_julia_file_on_markdown_headers(doc))

    # Alternatively, you can use the JuliaCodeSplitter
    # splitter = JuliaCodeSplitter(chunk_size=1000, chunk_overlap=100)
    # chunks = splitter.split_documents(docs)

    return chunks


def create_examples_retriever(
    dir_path: str = "./src/jutulgpt/rag_sources/jutuldarcy_examples/",
):
    loaded_examples_path = "./src/jutulgpt/rag_sources/loaded_examples.pkl"

    if os.path.exists(loaded_examples_path):
        with open(loaded_examples_path, "rb") as f:
            loaded = pickle.load(f)
    else:
        loader_examples = DirectoryLoader(
            path=dir_path,
            glob="**/*.jl",
            show_progress=True,
            loader_cls=UnstructuredFileLoader,
        )
        loaded = loader_examples.load()

        with open(loaded_examples_path, "wb") as f:
            pickle.dump(loaded, f)

    # Step 2: Split on markdown headers
    # header_chunks = []
    # for doc in loaded:
    #     header_chunks.extend(split_julia_file_on_markdown_headers(doc))
    index_chunks = []
    for doc in loaded:
        sections = split_julia_file_on_markdown_headers(doc)
        for section in sections:
            index_chunks.extend(JuliaCodeSplitter().split_documents([section]))

    # See header_chunks[i].page_content for the content of each chunk

    # Create  a vectorstore ret
    persist_directory = "./chroma_examples_dir"
    vectorstore = Chroma.from_documents(
        documents=index_chunks,
        embedding=embedding,
        persist_directory=persist_directory,
    )
    retriever = vectorstore.as_retriever()
    return retriever


examples_retriever = create_examples_retriever()
