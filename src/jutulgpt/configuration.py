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

from jutulgpt import prompts

# Static settings
cli_mode: bool = True


# Setup of the environment and some logging. Not neccessary to touch this.
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv()
_set_env("OPENAI_API_KEY")
logging.getLogger("httpx").setLevel(logging.WARNING)  # Less warnings in the output
logging.getLogger("faiss").setLevel(logging.WARNING)


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
        default=False,
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

    human_interaction: Annotated[
        bool,
        {"description": "Enable human-in-the-loop. Set to True when running the UI."},
    ] = field(
        default=True,
        metadata={
            "description": "Enable human-in-the-loop. Set to True when running the UI."
        },
    )

    embedding_model: Annotated[
        str,
        {"__template_metadata__": {"kind": "embeddings"}},
    ] = field(
        default_factory=lambda: "openai/text-embedding-3-small",
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

    search_type: Annotated[
        Literal["similarity", "mmr", "similarity_score_threshold"],
        {"__template_metadata__": {"kind": "reranker"}},
    ] = field(
        default="mmr",
        metadata={
            "description": "Defines the type of search that the retriever should perform."
        },
    )

    search_kwargs: dict[str, Any] = field(
        default_factory=lambda: {"k": 3, "fetch_k": 15, "lambda_mult": 0.5},
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
        default_factory=lambda: "openai/gpt-4.1-mini",
        metadata={
            "description": "The language model used for generating responses. Should be in the form: provider/model-name."
        },
    )

    supervisor_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = (
        field(
            default_factory=lambda: "openai/gpt-4.1-mini",
            metadata={
                "description": "The language model used as the supervisor in the multi-agent model."
            },
        )
    )
    coding_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default_factory=lambda: "openai/gpt-4.1-mini",
        metadata={"description": "The language model used for coding tasks."},
    )
    rag_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default_factory=lambda: "openai/gpt-4.1-mini",
        metadata={
            "description": "The language model used for retrieval-augmented generation."
        },
    )
    error_analyzer_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = (
        field(
            default_factory=lambda: "openai/gpt-4.1-mini",
            metadata={"description": "The language model used for error analysis."},
        )
    )

    # Prompts
    default_coder_prompt: str = field(
        default=prompts.DEFAULT_CODER_PROMPT,
        metadata={"description": "The default prompt used for generating Julia code."},
    )
    supervisor_prompt: str = field(
        default=prompts.SUPERVISOR_PROMPT,
        metadata={"description": "The prompt used for the supervisor agent."},
    )
    rag_prompt: str = field(
        default=prompts.RAG_PROMPT,
        metadata={"description": "The prompt used for the RAG agent."},
    )
    code_prompt: str = field(
        default=prompts.CODE_GENERATION_PROMPT,
        metadata={"description": "The prompt used for the coding agent."},
    )
    error_analyzer_prompt: str = field(
        default=prompts.ERROR_ANALYZER_PROMPT,
        metadata={
            "description": "The default prompt for analyzing the error messages and suggesting how to fix them."
        },
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
