"""Define the configurable parameters for the agent."""

from __future__ import annotations

import getpass
import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Optional

from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from jutulgpt import prompts


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


load_dotenv()
_set_env("OPENAI_API_KEY")

embedding_model = OpenAIEmbeddings()  # WARNING: TEMPORARY FIX
max_iterations = 3


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

    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/gpt-4.1",
        metadata={
            "description": "The name of the language model to use for the agent's main interactions. "
            "Should be in the form: provider/model-name."
        },
    )

    embedding_model: Annotated[
        str,
        {"__template_metadata__": {"kind": "embeddings"}},
    ] = field(
        default="openai/text-embedding-3-small",
        metadata={
            "description": "Name of the embedding model to use. Must be a valid embedding model name."
        },
    )

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

    def get_embedding_model(self) -> OpenAIEmbeddings:
        """Instantiate the embedding model based on the config."""
        if self.embedding_model.startswith("openai/"):
            model_name = self.embedding_model.split("/", 1)[1]
            return OpenAIEmbeddings(model=model_name)
        else:
            raise ValueError(f"Unsupported embedding model: {self.embedding_model}")
            raise ValueError(f"Unsupported embedding model: {self.embedding_model}")
