from dataclasses import dataclass
from functools import partial
from typing import Callable

from jutulgpt.configuration import (
    N_RETRIEVED_DOCS,
    N_RETRIEVED_EXAMPLES,
    PROJECT_ROOT,
    USE_LOCAL_MODEL,
)
from jutulgpt.rag import split_docs, split_examples


@dataclass
class RetrieverSpec:
    dir_path: str
    persist_path: str
    cache_path: str
    collection_name: str
    filetype: str
    split_func: Callable
    n_retrieved: int


retriever_dir_name = "ollama" if USE_LOCAL_MODEL else "openai"
RETRIEVER_SPECS = {
    "jutuldarcy": {
        "docs": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "docs" / "man"),
            persist_path=str(
                PROJECT_ROOT
                / "rag"
                / "retriever_store"
                / f"retriever_jutuldarcy_docs_{retriever_dir_name}"
            ),
            cache_path=str(
                PROJECT_ROOT / "rag" / "loaded_store" / "loaded_jutuldarcy_docs.pkl"
            ),
            collection_name="jutuldarcy_docs",
            filetype="md",
            split_func=split_docs.split_docs,
            n_retrieved=N_RETRIEVED_DOCS,
        ),
        "examples": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "examples"),
            persist_path=str(
                PROJECT_ROOT
                / "rag"
                / "retriever_store"
                / f"retriever_jutuldarcy_examples_{retriever_dir_name}"
            ),
            cache_path=str(
                PROJECT_ROOT / "rag" / "loaded_store" / "loaded_jutuldarcy_examples.pkl"
            ),
            collection_name="jutuldarcy_examples",
            filetype="jl",
            split_func=partial(
                split_examples.split_examples,
                header_to_split_on=2,  # Split on `# #` and `# ##`
            ),
            n_retrieved=N_RETRIEVED_EXAMPLES,
        ),
    },
    "fimbul": {
        "docs": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "fimbul" / "docs" / "man"),
            persist_path=str(
                PROJECT_ROOT
                / "rag"
                / "retriever_store"
                / f"retriever_fimbul_docs_{retriever_dir_name}"
            ),
            cache_path=str(
                PROJECT_ROOT / "rag" / "loaded_store" / "loaded_fimbul_docs.pkl"
            ),
            collection_name="fimbul_docs",
            filetype="md",
            split_func=split_docs.split_docs,
            n_retrieved=N_RETRIEVED_DOCS,
        ),
        "examples": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "fimbul" / "examples"),
            persist_path=str(
                PROJECT_ROOT
                / "rag"
                / "retriever_store"
                / f"retriever_fimbul_examples_{retriever_dir_name}"
            ),
            cache_path=str(
                PROJECT_ROOT / "rag" / "loaded_store" / "loaded_fimbul_examples.pkl"
            ),
            collection_name="fimbul_examples",
            filetype="jl",
            split_func=partial(
                split_examples.split_examples,
                header_to_split_on=1,  # Split on `# #`
            ),
            n_retrieved=N_RETRIEVED_EXAMPLES,
        ),
    },
}
