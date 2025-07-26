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

# Settings
USE_LOCAL_MODEL = (
    False  # Local models uses Ollama. Non-local models uses the OpenAI API
)
MAX_ITERATIONS = (
    3  # If the generated code fails. How many times the model will try to fix the code.
)
INTERACTIVE_ENVIRONMENT = True  # The human-in-the-loop works poorly in the terminal. Set to True when running the UI.
RETRIEVE_FIMBUL = True  # Whether to retrieve Fimbul documentation or not. If False, it will only retrieve JutulDarcy documentation.
ALLOW_PACKAGE_INSTALLATION = False  # Allow the agent to install packages. Set to False if you want to prevent this.
N_RETRIEVED_DOCS = 4  # Number of documents to retrieve in RAG.
N_RETRIEVED_EXAMPLES = 2  # Number of examples to retrieve in RAG.


# Setup of the environment and some logging. Not neccessary to touch this.
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv()
_set_env("OPENAI_API_KEY")
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("faiss").setLevel(logging.WARNING)


@dataclass(kw_only=True)
class BaseConfiguration:
    """Configuration class for indexing and retrieval operations.

    This class defines the parameters needed for configuring the indexing and
    retrieval processes, including embedding model selection, retriever provider choice, and search parameters.
    """

    embedding_model: Annotated[
        str,
        {"__template_metadata__": {"kind": "embeddings"}},
    ] = field(
        default="ollama/nomic-embed-text"
        if USE_LOCAL_MODEL
        else "openai/text-embedding-3-small",
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
            "description": "Defines the type of search that the Retriever should perform."
        },
    )

    search_kwargs: dict[str, Any] = field(
        default_factory=lambda: {
            "fetch_k": 15
        },  # NOTE: The "k" is set in the retriever specs by the N_RETRIEVED_DOCS and N_RETRIEVED_EXAMPLES variables.
        metadata={
            "description": "Additional keyword arguments to pass to the search function of the retriever. See langgraph documentation for details about what kwargs works for the different search types."
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
        default_factory=lambda: {"top_n": 3, "score_threshold": 0.75},
        metadata={"description": "Keyword arguments provided to the Flash reranker"},
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


@dataclass(kw_only=True)
class AgentConfiguration(BaseConfiguration):
    """The configuration for the agent."""

    # Models
    response_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="ollama/qwen3:14b" if USE_LOCAL_MODEL else "openai/gpt-4.1-mini",
        metadata={
            "description": "The language model used for generating responses. Should be in the form: provider/model-name."
        },
    )

    # Prompts
    default_coder_prompt: str = field(
        default=prompts.DEFAULT_CODER_PROMPT,
        metadata={"description": "The default prompt used for generating Julia code."},
    )
