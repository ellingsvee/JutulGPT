from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode
from typing_extensions import Sequence

from jutulgpt.configuration import BaseConfiguration
from jutulgpt.multi_agent_system.agents.agent_base import BaseAgent
from jutulgpt.state import State
from jutulgpt.tools.retrieve import (
    retrieve_fimbul_tool,
    retrieve_function_signature_tool,
    retrieve_jutuldarcy_tool,
)


class RAGAgent(BaseAgent):
    def __init__(
        self,
        tools: Optional[
            Union[Sequence[Union[BaseTool, Callable, dict[str, Any]]], ToolNode]
        ] = None,
        name: Optional[str] = None,
        part_of_multi_agent: bool = True,
        print_chat_output: bool = True,
    ):
        # Set default empty tools if none provided
        if tools is None:
            tools = []

        # Initialize the base agent
        super().__init__(
            tools=tools,
            name=name or "RAG Agent",
            part_of_multi_agent=part_of_multi_agent,
            state_schema=State,
            print_chat_output=print_chat_output,
        )

        self.user_provided_feedback = False

    def load_model(self, config: RunnableConfig) -> BaseChatModel:
        """
        Load the model from the name specified in the configuration.
        """
        configuration = BaseConfiguration.from_runnable_config(config)
        return self._setup_model(model=configuration.rag_model)

    def get_prompt_from_config(self, config: RunnableConfig) -> str:
        """
        Get the prompt from the configuration.

        Returns:
            A string containing the spesific prompt from the config
        """
        configuration = BaseConfiguration.from_runnable_config(config)
        return configuration.rag_prompt


rag_agent = RAGAgent(
    part_of_multi_agent=True,
    tools=[
        retrieve_fimbul_tool,
        retrieve_function_signature_tool,
        retrieve_jutuldarcy_tool,
    ],
    name="rag_agent",
    print_chat_output=False,
)
rag_graph = rag_agent.graph
