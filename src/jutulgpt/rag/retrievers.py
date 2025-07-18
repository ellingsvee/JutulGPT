import os
import pickle
import re
from abc import ABC
from collections import defaultdict
from os.path import splitroot
from typing import Callable, List

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from jutulgpt.configuration import (
    PROJECT_ROOT,
    compressor,
    embedding_model,
    static_config,
)
from jutulgpt.rag import split_docs, split_examples
from jutulgpt.utils import deduplicate_document_chunks

# import format_doc, split_docs, split_examples

# import format_doc, split_docs, split_examples


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


class Indexer:
    def __init__(
        self,
        embedding_model,
        split_func: Callable,
        filetype: str,
        dir_path: str,
        persist_path: str,
        cache_path: str,
        collection_name: str = "default_collection",
    ):
        self.dir_path = dir_path
        self.persist_path = persist_path
        self.cache_path = cache_path
        self.embedding_model = embedding_model
        self.split_func = split_func
        self.filetype = filetype
        self.collection_name = collection_name

    def load(self):
        loader = DirectoryLoader(
            path=self.dir_path,
            glob=f"**/*.{self.filetype}",
            show_progress=True,
            loader_cls=TextLoader,
        )
        return _load_or_retrieve_from_storage(loader, self.cache_path)

    def split(self, docs: List[Document]) -> List[Document]:
        chunks = []
        for doc in docs:
            chunks.extend(self.split_func(doc))
        return chunks

    def get_retriever(self):
        if os.path.exists(self.persist_path):
            print(f"Loading existing FAISS index from {self.persist_path}")
            vectorstore = FAISS.load_local(
                self.persist_path,
                self.embedding_model,
                allow_dangerous_deserialization=True,
            )
        else:
            print(f"Creating new FAISS index at {self.persist_path}")
            docs = self.split(self.load())
            vectorstore = FAISS.from_documents(
                documents=docs,
                embedding=self.embedding_model,
            )
            vectorstore.save_local(self.persist_path)
        return vectorstore.as_retriever(search_kwargs={"k": 8})


faiss_dir_name = "openai" if static_config.use_openai else "ollama"
jutuldarcy_examples_indexer = Indexer(
    embedding_model=embedding_model,
    split_func=split_examples.split_examples,
    filetype="jl",
    dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "examples"),
    persist_path=str(
        PROJECT_ROOT
        / "rag"
        / "faiss_store"
        / f"faiss_jutuldarcy_examples_{faiss_dir_name}"
    ),
    cache_path=str(
        PROJECT_ROOT / "rag" / "loaded_store" / "loaded_jutuldarcy_examples.pkl"
    ),
    collection_name="jutuldarcy_examples",
)

jutuldarcy_docs_indexer = Indexer(
    embedding_model=embedding_model,
    split_func=split_docs.split_docs,
    filetype="md",
    dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "docs" / "man"),
    persist_path=str(
        PROJECT_ROOT / "rag" / "faiss_store" / f"faiss_jutuldarcy_docs_{faiss_dir_name}"
    ),
    cache_path=str(
        PROJECT_ROOT / "rag" / "loaded_store" / "loaded_jutuldarcy_docs.pkl"
    ),
    collection_name="jutuldarcy_docs",
)

fimbul_examples_indexer = Indexer(
    embedding_model=embedding_model,
    split_func=split_examples.split_examples,
    filetype="jl",
    dir_path=str(PROJECT_ROOT / "rag" / "fimbul" / "examples"),
    persist_path=str(
        PROJECT_ROOT / "rag" / "faiss_store" / f"faiss_fimbul_examples_{faiss_dir_name}"
    ),
    cache_path=str(
        PROJECT_ROOT / "rag" / "loaded_store" / "loaded_fimbul_examples.pkl"
    ),
    collection_name="fimbul_examples",
)

fimbul_docs_indexer = Indexer(
    embedding_model=embedding_model,
    split_func=split_docs.split_docs,
    filetype="md",
    dir_path=str(PROJECT_ROOT / "rag" / "fimbul" / "docs" / "man"),
    persist_path=str(
        PROJECT_ROOT / "rag" / "faiss_store" / f"faiss_fimbul_docs_{faiss_dir_name}"
    ),
    cache_path=str(PROJECT_ROOT / "rag" / "loaded_store" / "loaded_fimbul_docs.pkl"),
    collection_name="fimbul_docs",
)


def get_retrievers():
    def apply_compressor(compressor, retriever):
        return ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=retriever
        )

    jutuldarcy_docs_retriever = apply_compressor(
        compressor, jutuldarcy_docs_indexer.get_retriever()
    )
    jutuldarcy_examples_retriever = apply_compressor(
        compressor, jutuldarcy_examples_indexer.get_retriever()
    )
    fimbul_docs_retriever = apply_compressor(
        compressor, fimbul_docs_indexer.get_retriever()
    )
    fimbul_examples_retriever = apply_compressor(
        compressor, fimbul_examples_indexer.get_retriever()
    )

    jutuldarcy = {
        "docs": jutuldarcy_docs_retriever,
        "examples": jutuldarcy_examples_retriever,
    }
    fimbul = {
        "docs": fimbul_docs_retriever,
        "examples": fimbul_examples_retriever,
    }
    return {
        "jutuldarcy": jutuldarcy,
        "fimbul": fimbul,
    }


retrievers = get_retrievers()


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


# def format_docs(docs, n: int = 5, remove_duplicates: bool = True):
#     if remove_duplicates:
#         docs = deduplicate_document_chunks(docs)
#     docs = docs[:n]

#     formatted = []
#     for doc in docs:
#         doc_string = ""
#         # file_source, section_path = split_docs.get_file_source_and_section_path(doc)
#         file_source = split_docs.get_file_source(doc)
#         section_path = split_docs.get_section_path(doc)
#         doc_string += f"# From `{file_source}`\n# Section: `{section_path}`\n"
#         doc_string += f"{split_docs.format_doc(doc)}"
#         formatted.append(doc_string)
#     return "\n\n".join(formatted)
