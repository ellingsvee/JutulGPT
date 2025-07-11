"""Define the configurable parameters for the agent."""

from __future__ import annotations

import getpass
import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Optional, Union

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from jutulgpt import prompts


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


load_dotenv()
_set_env("OPENAI_API_KEY")

use_openai = True
# embedding_model = OpenAIEmbeddings()  # WARNING: TEMPORARY FIX
max_iterations = 2
check_code_bool = True
retrieve_jutuldacy = True
retrieve_fimbul = True


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    system_prompt: str = field(
        default=prompts.AGENT_SYSTEM,
        metadata={
            "description": "The system prompt to use for the agent's interactions. "
            "This prompt sets the context and behavior for the agent."
        },
    )

    if use_openai:
        default_model_name = "openai/gpt-4.1-mini"
    else:
        default_model_name = "ollama/qwen2.5:32b"

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=default_model_name,
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    # if use_openai:
    #     default_embedding_name = "openai/text-embedding-3-small"
    # else:
    #     default_embedding_name = "ollama/nomic-embed-text"

    # embedding_model: Annotated[
    #     str,
    #     {"__template_metadata__": {"kind": "embeddings"}},
    # ] = field(
    #     default=default_embedding_name,
    #     metadata={
    #         "description": "Name of the embedding model to use. Must be a valid embedding model name."
    #     },
    # )

    # embedding_model = OpenAIEmbeddings()

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


if use_openai:
    default_embedding_name = "openai/text-embedding-3-small"
else:
    default_embedding_name = "ollama/nomic-embed-text"

# embedding_model_name: Annotated[
#     str,
#     {"__template_metadata__": {"kind": "embeddings"}},
# ] = field(
#     default=default_embedding_name,
#     metadata={
#         "description": "Name of the embedding model to use. Must be a valid embedding model name."
#     },
# )
embedding_model_name = default_embedding_name


def get_embedding_model(
    embedding_model_name: str,
) -> Union[OpenAIEmbeddings, OllamaEmbeddings]:
    """Instantiate the embedding model based on the config."""

    provider, model = embedding_model_name.split("/", maxsplit=1)
    if provider == "openai":
        return OpenAIEmbeddings(model=model)
    elif provider == "ollama":
        return OllamaEmbeddings(model=model)

    else:
        raise ValueError(f"Unsupported embedding model: {embedding_model_name}")


embedding_model = get_embedding_model(embedding_model_name)
