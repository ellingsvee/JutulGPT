import os
from contextlib import contextmanager
from typing import Generator, List, Union

from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import FlashrankRerank
from langchain_core.embeddings import Embeddings
from langchain_core.runnables import RunnableConfig
from langchain_core.vectorstores import VectorStoreRetriever

# from langchain_core.documents import BaseDocumentCompressor
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.rag.retriever_specs import RetrieverSpec
from jutulgpt.utils import get_provider_and_model


def make_text_encoder(model: str) -> Embeddings:
    """Connect to the configured text encoder."""
    provider, model = model.split("/", maxsplit=1)
    match provider:
        case "openai":
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(model=model)
        case "ollama":
            from langchain_ollama import OllamaEmbeddings

            return OllamaEmbeddings(model=model)

        case _:
            raise ValueError(f"Unsupported embedding provider: {provider}")


def _load_and_split_docs(spec: RetrieverSpec) -> list:
    import pickle

    from langchain_community.document_loaders import DirectoryLoader, TextLoader

    # Load or cache documents
    loader = DirectoryLoader(
        path=spec.dir_path,
        glob=f"**/*.{spec.filetype}",
        show_progress=True,
        loader_cls=TextLoader,
    )

    if os.path.exists(spec.cache_path):
        with open(spec.cache_path, "rb") as f:
            docs = pickle.load(f)
    else:
        docs = loader.load()

        with open(spec.cache_path, "wb") as f:
            pickle.dump(docs, f)

    # Split documents
    chunks = []
    for doc in docs:
        chunks.extend(spec.split_func(doc))
    return chunks


@contextmanager
def make_faiss_retriever(
    configuration: BaseConfiguration,
    spec: RetrieverSpec,
    embedding_model: Embeddings,
    search_type: str,
    search_kwargs: dict,
) -> Generator[VectorStoreRetriever, None, None]:
    """
    Create or load a FAISS retriever, saving the index locally to avoid re-indexing.
    Uses configuration to determine file paths and splitting functions.
    """
    import os

    from langchain_community.vectorstores import FAISS

    # Get the persist path by checking what is the specified embedding model
    persist_path = spec.persist_path(
        get_provider_and_model(configuration.embedding_model)[0]
    )

    # Load or create FAISS index
    if os.path.exists(persist_path):
        vectorstore = FAISS.load_local(
            persist_path,
            embedding_model,
            allow_dangerous_deserialization=True,
        )
    else:
        print(f"Creating new FAISS index at {spec.persist_path}")
        docs = _load_and_split_docs(spec)
        vectorstore = FAISS.from_documents(
            documents=docs,
            embedding=embedding_model,
        )
        vectorstore.save_local(persist_path)

    yield vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs={**search_kwargs},
    )


@contextmanager
def make_chroma_retriever(
    configuration: BaseConfiguration,
    spec: RetrieverSpec,
    embedding_model: Embeddings,
    search_type: str,
    search_kwargs: dict,
) -> Generator[VectorStoreRetriever, None, None]:
    """
    Create or load a FAISS retriever, saving the index locally to avoid re-indexing.
    Uses configuration to determine file paths and splitting functions.
    """
    import os

    from langchain_chroma import Chroma

    # Get the persist path by checking what is the specified embedding model
    persist_path = spec.persist_path(
        get_provider_and_model(configuration.embedding_model)[0]
    )

    # Load or create FAISS index
    if os.path.exists(persist_path):
        vectorstore = Chroma(
            embedding_function=embedding_model,
            persist_directory=persist_path,
            collection_name=spec.collection_name,
        )

    else:
        print(f"Creating new Chroma index at {persist_path}")
        docs = _load_and_split_docs(spec)

        vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=embedding_model,
            persist_directory=persist_path,
            collection_name=spec.collection_name,
        )

    yield vectorstore.as_retriever(
        search_type=search_type,
        search_kwargs={**search_kwargs},
    )


def apply_flash_reranker(
    configuration: BaseConfiguration, retriever: VectorStoreRetriever
):
    compressor = FlashrankRerank(**configuration.rerank_kwargs)

    return ContextualCompressionRetriever(
        base_compressor=compressor, base_retriever=retriever
    )


@contextmanager
def make_retriever(
    config: RunnableConfig,
    spec: RetrieverSpec,
    **retrieval_overrides,
) -> Generator[Union[VectorStoreRetriever, ContextualCompressionRetriever], None, None]:
    """
    Create a retriever for the agent, based on the current configuration.

    Args:
        config: The runnable configuration
        spec: The retriever specification
        **retrieval_overrides: Override any retrieval parameters (search_type, search_kwargs, etc.)
    """
    configuration = BaseConfiguration.from_runnable_config(config)

    # Merge configuration defaults with any overrides
    retrieval_params = {
        "search_type": configuration.search_type,
        "search_kwargs": configuration.search_kwargs,
        **retrieval_overrides,
    }

    embedding_model = make_text_encoder(configuration.embedding_model)

    # Get the retriever
    selected_retriever = None
    match configuration.retriever_provider:
        case "faiss":
            with make_faiss_retriever(
                configuration,
                spec,
                embedding_model,
                retrieval_params["search_type"],
                retrieval_params["search_kwargs"],
            ) as retriever:
                selected_retriever = retriever
        case "chroma":
            with make_chroma_retriever(
                configuration,
                spec,
                embedding_model,
                retrieval_params["search_type"],
                retrieval_params["search_kwargs"],
            ) as retriever:
                selected_retriever = retriever

        case _:
            raise ValueError(
                "Unrecognized retriever_provider in configuration. "
                f"Expected one of: {', '.join(BaseConfiguration.__annotations__['retriever_provider'].__args__)}\n"
                f"Got: {configuration.retriever_provider}"
            )

    # Apply the reranker
    match configuration.rerank_provider:
        case "flash":
            yield apply_flash_reranker(configuration, selected_retriever)
        case "None":
            yield selected_retriever
        case _:
            raise ValueError(
                "Unrecognized rerank_provider in configuration. "
                f"Expected one of: {', '.join(BaseConfiguration.__annotations__['rerank_provider'].__args__)}\n"
                f"Got: {configuration.rerank_provider}"
            )
