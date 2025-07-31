"""
File for defining the specifics related to the different retrievers. Gives flexibility to vary the splitting functions etc.
"""

from dataclasses import dataclass
from functools import partial
from typing import Callable

from jutulgpt.configuration import PROJECT_ROOT
from jutulgpt.rag import split_docs, split_examples, split_function_signatures


@dataclass
class RetrieverSpec:
    dir_path: str
    persist_path: Callable  # Callable as we want to change where we store when we modify the embedding model in the configuration.
    cache_path: str
    collection_name: str
    filetype: str
    split_func: Callable


RETRIEVER_SPECS = {
    "jutuldarcy": {
        "docs": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "docs" / "man"),
            persist_path=lambda retriever_dir_name: str(
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
            split_func=partial(
                split_docs.split_docs,
                headers_to_split_on=[
                    ("#", "Header 1"),
                ],
            ),
        ),
        "function_signatures": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "function_signatures"),
            persist_path=lambda retriever_dir_name: str(
                PROJECT_ROOT
                / "rag"
                / "retriever_store"
                / f"retriever_jutuldarcy_function_signatures_{retriever_dir_name}"
            ),
            cache_path=str(
                PROJECT_ROOT
                / "rag"
                / "loaded_store"
                / "loaded_jutuldarcy_function_signatures.pkl"
            ),
            collection_name="jutuldarcy_function_signatures",
            filetype="md",
            split_func=split_function_signatures.split_function_signatures,
        ),
        "examples": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "jutuldarcy" / "examples"),
            persist_path=lambda retriever_dir_name: str(
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
                header_to_split_on=1,  # Split on `# #`
            ),
        ),
    },
    "fimbul": {
        "docs": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "fimbul" / "docs" / "man"),
            persist_path=lambda retriever_dir_name: str(
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
            split_func=partial(
                split_docs.split_docs,
                headers_to_split_on=[
                    ("#", "Header 1"),
                ],
            ),
        ),
        "examples": RetrieverSpec(
            dir_path=str(PROJECT_ROOT / "rag" / "fimbul" / "examples"),
            persist_path=lambda retriever_dir_name: str(
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
        ),
    },
}
