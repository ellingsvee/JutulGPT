import os
import pickle
import re
from abc import ABC
from collections import defaultdict
from typing import List

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
)
from langchain_core.documents import Document
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from jutulgpt.config import embedding


def _deduplicate_chunks(chunks):
    seen = set()
    deduped = []
    for doc in chunks:
        content = doc.page_content.strip()
        if content not in seen:
            seen.add(content)
            deduped.append(doc)
    return deduped


def format_examples(
    docs: List[Document], n: int = 2, remove_duplicates: bool = True
) -> str:
    if remove_duplicates:
        docs = _deduplicate_chunks(docs)

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
        section = "\n".join(contents)
        formatted.append(f"## From `{source}` — Section: `{heading}`\n{section}")
    return "\n\n---\n\n".join(formatted)


def _load_or_retrieve_from_storage(
    loader: DirectoryLoader, storage_path: str
) -> List[Document]:
    if os.path.exists(storage_path):
        # if False:
        with open(storage_path, "rb") as f:
            loaded = pickle.load(f)
    else:
        loaded = loader.load()

        with open(storage_path, "wb") as f:
            pickle.dump(loaded, f)
    return loaded


def _split_julia_file_on_markdown_headers(document: Document) -> List[Document]:
    """
    Splits a Document at lines like `# #` or `# ##`, which represent markdown headings
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


def _split_markdown_file(
    markdown_splitter: MarkdownHeaderTextSplitter,
    text_splitter: RecursiveCharacterTextSplitter,
    document: Document,
) -> List[Document]:
    content = document.page_content
    document_metadata = document.metadata.copy()

    splits = markdown_splitter.split_text(content)
    for split in splits:
        split.metadata = {**split.metadata, **document_metadata}

    splits = text_splitter.split_documents(splits)

    return splits


def _format_doc(doc: Document) -> str:
    header_keys = ["Header 1", "Header 2"]
    section_path_parts = [
        str(doc.metadata[k])
        for k in header_keys
        if k in doc.metadata and doc.metadata[k] is not None
    ]
    section_path = " > ".join(section_path_parts) if section_path_parts else "Root"
    file_source = doc.metadata.get("source", "Unknown Document")
    return f"## From `{file_source}` - Section: `{section_path}`\n{doc.page_content.strip()}"


def format_docs(docs, n: int = 2, remove_duplicates: bool = True):
    if remove_duplicates:
        docs = _deduplicate_chunks(docs)
    docs = docs[:n]

    formatted = [_format_doc(doc) for doc in docs]
    return "\n\n---\n\n".join(formatted)


class BaseIndexer(ABC):
    def __init__(
        self,
        dir_path: str,
        persist_path: str,
        cache_path: str,
    ):
        self.dir_path = dir_path
        self.persist_path = persist_path
        self.cache_path = cache_path

    def load(self) -> List[Document]:
        raise NotImplementedError("Subclasses should implement this method.")

    def split(self, docs: List[Document]) -> List[Document]:
        raise NotImplementedError("Subclasses should implement this method.")

    def get_retriever(self):
        raise NotImplementedError("Subclasses should implement this method.")


class JuliaExampleIndexer(BaseIndexer):
    def __init__(
        self,
        dir_path: str = "./src/jutulgpt/rag_sources/jutuldarcy_examples/",
        persist_path: str = "./src/jutulgpt/rag_sources/chroma_examples",
        cache_path: str = "./src/jutulgpt/rag_sources/loaded_examples.pkl",
    ):
        super().__init__(dir_path, persist_path, cache_path)

    def load(self):
        loader = DirectoryLoader(
            path=self.dir_path,
            glob="**/*.jl",
            show_progress=True,
            loader_cls=TextLoader,
        )
        return _load_or_retrieve_from_storage(loader, self.cache_path)

    def split(self, docs: List[Document]) -> List[Document]:
        chunks = []
        for doc in docs:
            chunks.extend(_split_julia_file_on_markdown_headers(doc))
        return chunks

    def get_retriever(self):
        docs = self.split(self.load())

        if os.path.exists(self.persist_path):
            vectorstore = Chroma(
                embedding_function=embedding,
                persist_directory=self.persist_path,
                collection_name="jutuldarcy_examples",
            )
        else:
            vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=embedding,
                persist_directory=self.persist_path,
                collection_name="jutuldarcy_examples",
            )
        return vectorstore.as_retriever(search_kwargs={"k": 8})


class MarkdownDocIndexer(BaseIndexer):
    def __init__(
        self,
        dir_path: str = "./src/jutulgpt/rag_sources/jutuldarcy_docs/man/",
        persist_path: str = "./src/jutulgpt/rag_sources/chroma_docs",
        cache_path: str = "./src/jutulgpt/rag_sources/loaded_docs.pkl",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        super().__init__(dir_path, persist_path, cache_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
            ],
            strip_headers=False,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

    def load(self):
        loader = DirectoryLoader(
            path=self.dir_path,
            glob="**/*.md",
            show_progress=True,
            loader_cls=TextLoader,
        )
        return _load_or_retrieve_from_storage(loader, self.cache_path)

    def split(self, docs: List[Document]) -> List[Document]:
        chunks = []
        for doc in docs:
            chunks.extend(
                _split_markdown_file(
                    markdown_splitter=self.markdown_splitter,
                    text_splitter=self.text_splitter,
                    document=doc,
                )
            )
        return chunks

    def get_retriever(self):
        docs = self.split(self.load())

        if os.path.exists(self.persist_path):
            vectorstore = Chroma(
                embedding_function=embedding,
                persist_directory=self.persist_path,
                collection_name="jutuldarcy_docs",
            )
        else:
            vectorstore = Chroma.from_documents(
                documents=docs,
                embedding=embedding,
                persist_directory=self.persist_path,
                collection_name="jutuldarcy_docs",
            )

        return vectorstore.as_retriever(search_kwargs={"k": 8})


examples_indexer = JuliaExampleIndexer()
examples_retriever = examples_indexer.get_retriever()

docs_indexer = MarkdownDocIndexer()
docs_retriever = docs_indexer.get_retriever()
