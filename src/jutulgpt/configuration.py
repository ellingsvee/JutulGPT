"""Define the configurable parameters for the agent."""

from __future__ import annotations

import getpass
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
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

PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass(kw_only=True)
class Configuration:
    """The configuration for the agent."""

    use_openai = True
    max_iterations = 2

    check_code_bool = True
    ask_before_check_code = True

    retrieve_jutuldacy = True
    retrieve_fimbul = False

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

    if use_openai:
        default_embedding_name = "openai/text-embedding-3-small"
    else:
        default_embedding_name = "ollama/nomic-embed-text"

    embedding_model = default_embedding_name

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> Configuration:
        """Create a Configuration instance from a RunnableConfig object."""
        config = ensure_config(config)
        configurable = config.get("configurable") or {}
        _fields = {f.name for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in configurable.items() if k in _fields})


static_config = Configuration()
