from __future__ import annotations

from typing import Any, Callable, Literal, Optional, Sequence, Union

from langchain_core.language_models import LanguageModelLike
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from jutulgpt.agents.agent_base import BaseAgent
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.nodes import check_code
from jutulgpt.state import State
from jutulgpt.tools import (
    grep_search_tool,
    read_file_tool,
    retrieve_function_documentation_tool,
    retrieve_jutuldarcy_examples_tool,
)
from jutulgpt.utils import get_code_from_response


class Agent(BaseAgent):
    def __init__(
        self,
        tools: Optional[
            Union[Sequence[Union[BaseTool, Callable, dict[str, Any]]], ToolNode]
        ] = None,
        name: Optional[str] = None,
        print_chat_output: bool = True,
        filepath: Optional[str] = None,
    ):
        # Set default empty tools if none provided
        if tools is None:
            tools = []

        # Initialize the base agent
        super().__init__(
            tools=tools,
            name=name or "Agent",
            printed_name="Agent",
            part_of_multi_agent=False,
            state_schema=State,
            print_chat_output=print_chat_output,
            filepath=filepath,
        )

        self.user_provided_feedback = False

    def build_graph(self):
        """Build the react agent graph."""

        workflow = StateGraph(self.state_schema, config_schema=BaseConfiguration)

        # Add nodes
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("finalize", self.finalize)
        workflow.add_node("check_code", check_code)

        # Set entry point
        if cli_mode:
            workflow.add_node("get_user_input", self.get_user_input)
            workflow.set_entry_point("get_user_input")
            workflow.add_edge("get_user_input", "agent")
        else:
            workflow.set_entry_point("agent")

        # Add edges
        workflow.add_edge("tools", "agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                "continue": "check_code",
            },
        )
        workflow.add_conditional_edges(
            "check_code",
            self.direct_after_check_code,
            {
                "agent": "agent",
                "finalize": "finalize",
            },
        )
        workflow.add_edge("finalize", "get_user_input")

        # Compile with memory if standalone
        return workflow.compile()

    def get_model_from_config(
        self, config: RunnableConfig
    ) -> Union[str, LanguageModelLike]:
        configuration = BaseConfiguration.from_runnable_config(config)
        return configuration.coding_model

    def get_prompt_from_config(self, config: RunnableConfig) -> str:
        """
        Get the prompt from the configuration.

        Returns:
            A string containing the spesific prompt from the config
        """
        configuration = BaseConfiguration.from_runnable_config(config)
        return configuration.agent_prompt

    def call_model(self, state: State, config: RunnableConfig) -> dict:
        """Call the model with the current state."""

        response = self.invoke_model(state=state, config=config)

        # Check if we need more steps
        if self._are_more_steps_needed(state, response):
            return {
                "messages": [
                    AIMessage(
                        id=response.id,
                        content="Sorry, need more steps to process this request.",
                    )
                ]
            }

        code_block = get_code_from_response(response=response.content)

        return {"messages": [response], "code_block": code_block, "error": False}

    def finalize(self, state: State, config: RunnableConfig):
        self.write_julia_code_to_file(code_block=state.code_block)
        return {}

    def direct_after_user_feedback_on_generated_code(
        self, state: State
    ) -> Literal["agent", "check_code"]:
        if self.user_provided_feedback:
            self.user_provided_feedback = False
            return "agent"
        return "check_code"

    def direct_after_check_code(
        self, state: State, config: RunnableConfig
    ) -> Literal["agent", "finalize"]:
        if state.error:
            return "agent"
        return "finalize"

    def decide_to_finish(
        self, state: State, config: RunnableConfig
    ) -> Literal["call_model", "end"]:
        return "end"


agent = Agent(
    tools=[
        retrieve_jutuldarcy_examples_tool,
        retrieve_function_documentation_tool,
        read_file_tool,
        grep_search_tool,
    ],
    name="Agent",
    print_chat_output=True,
)
