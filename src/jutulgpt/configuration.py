"""Define the configurable parameters for the agent."""

from __future__ import annotations

import getpass
import logging
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Type, TypeVar

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig, ensure_config
from pydantic import BaseModel, ConfigDict

from jutulgpt import prompts

# Static settings
cli_mode: bool = True

# Select whether to use local models through Ollama or use OpenAI
LOCAL_MODELS = False
LLM_MODEL_NAME = "ollama:qwen3:14b" if LOCAL_MODELS else "openai:gpt-4.1"


EMBEDDING_MODEL_NAME = (
    "ollama:nomic-embed-text" if LOCAL_MODELS else "openai:text-embedding-3-small"
)

RECURSION_LIMIT = 200  # Number of recursions before an error is thrown.
LLM_TEMPERATURE = 0


# Setup of the environment and some logging. Not neccessary to touch this.
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv()
_set_env("OPENAI_API_KEY")
logging.getLogger("httpx").setLevel(logging.WARNING)  # Less warnings in the output
logging.getLogger("faiss").setLevel(logging.WARNING)


class HumanInteraction(BaseModel):
    model_config = ConfigDict(extra="forbid")  # optional strictness
    rag_query: bool = field(
        default=False,
        metadata={"description": "Whether to modify the generated RAG query."},
    )
    retrieved_documents: bool = field(
        default=False,
        metadata={
            "description": "Whether to verify and filter the retrieved documents."
        },
    )
    retrieved_examples: bool = field(
        default=False,
        metadata={
            "description": "Whether to verify and filter the retrieved examples."
        },
    )
    generated_code: bool = field(
        default=False,
        metadata={
            "description": "Whether to verify the generated code, edit it manually, or request a fix."
        },
    )
    code_check: bool = field(
        default=True,
        metadata={
            "description": "Whether to perform code checks on the generated code."
        },
    )
    fix_error: bool = field(
        default=False,
        metadata={
            "description": "Whether to decide to try to fix errors in the generated code."
        },
    )


@dataclass(kw_only=True)
class BaseConfiguration:
    """Configuration class for indexing and retrieval operations.

    This class defines the parameters needed for configuring the indexing and
    retrieval processes, including embedding model selection, retriever provider choice, and search parameters.
    """

    use_local_model: Annotated[
        bool,
        {
            "description": "If True, use local models (Ollama). If False, use OpenAI API."
        },
    ] = field(
        default=LOCAL_MODELS,
        metadata={
            "description": "If True, use local models (Ollama). If False, use OpenAI API."
        },
    )

    retrieve_fimbul: Annotated[
        bool,
        {
            "description": "Whether to retrieve Fimbul documentation or not. If False, only JutulDarcy documentation is retrieved."
        },
    ] = field(
        default=False,
        metadata={
            "description": "Whether to retrieve Fimbul documentation or not. If False, only JutulDarcy documentation is retrieved."
        },
    )

    max_iterations: Annotated[
        int,
        {
            "description": "How many times the model will try to fix the code if it fails."
        },
    ] = field(
        default=3,
        metadata={
            "description": "How many times the model will try to fix the code if it fails."
        },
    )

    human_interaction: HumanInteraction = field(
        default_factory=HumanInteraction,
        metadata={
            "description": "Configuration for human interaction during the process. "
            "This includes options for RAG queries, retrieved documents, code checks, and multi-agent saving."
        },
    )

    embedding_model: Annotated[
        str,
        {"__template_metadata__": {"kind": "embeddings"}},
    ] = field(
        default_factory=lambda: EMBEDDING_MODEL_NAME,
        metadata={
            "description": "Name of the embedding model to use. Must be a valid embedding model name."
        },
    )

    retriever_provider: Annotated[
        Literal["faiss", "chroma"],
        {"__template_metadata__": {"kind": "retriever"}},
    ] = field(
        default="chroma",
        metadata={"description": "The vector store provider to use for retrieval."},
    )

    documents_search_type: Annotated[
        Literal["similarity", "mmr", "similarity_score_threshold"],
        {"__template_metadata__": {"kind": "reranker"}},
    ] = field(
        default="similarity",
        metadata={
            "description": "Defines the type of search that the retriever should perform."
        },
    )

    documents_search_kwargs: dict[str, Any] = field(
        # default_factory=lambda: {"score_threshold": 0.2},
        default_factory=lambda: {"k": 5},
        metadata={
            "description": "Additional keyword arguments to pass to the search function of the retriever. See langgraph documentation for details about what kwargs works for the different search types. See https://python.langchain.com/api_reference/chroma/vectorstores/langchain_chroma.vectorstores.Chroma.html#langchain_chroma.vectorstores.Chroma.as_retriever"
        },
    )

    examples_search_type: Annotated[
        Literal["similarity", "mmr", "similarity_score_threshold"],
        {"__template_metadata__": {"kind": "reranker"}},
    ] = field(
        default="mmr",
        metadata={
            "description": "Defines the type of search that the retriever should perform."
        },
    )

    examples_search_kwargs: dict[str, Any] = field(
        default_factory=lambda: {"k": 2, "fetch_k": 10, "lambda_mult": 0.5},
        metadata={
            "description": "Additional keyword arguments to pass to the search function of the retriever. See langgraph documentation for details about what kwargs works for the different search types. See https://python.langchain.com/api_reference/chroma/vectorstores/langchain_chroma.vectorstores.Chroma.html#langchain_chroma.vectorstores.Chroma.as_retriever"
        },
    )

    rerank_provider: Annotated[
        Literal["None", "flash"],
        {"__template_metadata__": {"kind": "reranker"}},
    ] = field(
        default="None",
        metadata={
            "description": "The provider user for reranking the retrieved documents."
        },
    )

    rerank_kwargs: dict[str, Any] = field(
        default_factory=lambda: {},
        metadata={"description": "Keyword arguments provided to the reranker"},
    )

    # Models
    response_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default_factory=lambda: LLM_MODEL_NAME,
        metadata={
            "description": "The language model used for generating responses. Should be in the form: provider/model-name."
        },
    )

    supervisor_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = (
        field(
            default_factory=lambda: LLM_MODEL_NAME,
            metadata={
                "description": "The language model used as the supervisor in the multi-agent model."
            },
        )
    )
    coding_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default_factory=lambda: LLM_MODEL_NAME,
        metadata={"description": "The language model used for coding tasks."},
    )
    rag_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default_factory=lambda: LLM_MODEL_NAME,
        metadata={
            "description": "The language model used for retrieval-augmented generation."
        },
    )
    error_analyzer_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = (
        field(
            default_factory=lambda: LLM_MODEL_NAME,
            metadata={"description": "The language model used for error analysis."},
        )
    )

    # Prompts
    agent_prompt: str = field(
        default=prompts.AGENT_PROMPT,
        metadata={"description": "The default prompt used for the agent."},
    )
    rag_prompt: str = field(
        default=prompts.RAG_PROMPT,
        metadata={"description": "The prompt used for the RAG agent."},
    )
    code_prompt: str = field(
        default=prompts.CODE_PROMPT,
        metadata={"description": "The prompt used for the coding agent."},
    )

    @classmethod
    def from_runnable_config(
        cls: Type[T], config: Optional[RunnableConfig] = None
    ) -> T:
        """Create an IndexConfiguration instance from a RunnableConfig object.

        Args:
            cls (Type[T]): The class itself.
            config (Optional[RunnableConfig]): The configuration object to use.

        Returns:
            T: An instance of IndexConfiguration with the specified configuration.
        """
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


T = TypeVar("T", bound=BaseConfiguration)
