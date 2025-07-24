from dataclasses import dataclass
from typing import Callable

from jutulgpt.configuration import PROJECT_ROOT, USE_LOCAL_MODEL
from jutulgpt.rag import split_docs, split_examples


@dataclass
class RetrieverSpec:
    dir_path: str
    persist_path: str
    cache_path: str
    collection_name: str
    filetype: str
    split_func: Callable


faiss_dir_name = "ollama" if USE_LOCAL_MODEL else "openai"
RETRIEVER_SPECS = {
    "jutuldarcy": {
        "docs": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "docs" / "man"),
            persist_path=str(
                PROJECT_ROOT
                / "rag"
                / "faiss_store"
                / f"faiss_jutuldarcy_docs_{faiss_dir_name}"
            ),
            cache_path=str(
                PROJECT_ROOT / "rag" / "loaded_store" / "loaded_jutuldarcy_docs.pkl"
            ),
            collection_name="jutuldarcy_docs",
            filetype="md",
            split_func=split_docs.split_docs,
        ),
        "examples": RetrieverSpec(
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
            filetype="jl",
            split_func=split_examples.split_examples,
        ),
    }
}
