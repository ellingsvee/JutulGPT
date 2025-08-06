from __future__ import annotations

from typing import Any, Callable, List, Literal, Optional, Sequence, Union, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.cli.cli_human_interaction import (
    cli_response_on_generated_code,
)
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.human_in_the_loop import response_on_generated_code
from jutulgpt.multi_agent_system.agents.agent_base import BaseAgent
from jutulgpt.nodes import check_code, get_relevant_function_documentation
from jutulgpt.state import State
from jutulgpt.tools import (
    read_from_file_tool,
    retrieve_fimbul_tool,
    retrieve_function_signature_tool,
    retrieve_jutuldarcy_tool,
    write_to_file_tool,
)
from jutulgpt.utils import (
    get_code_from_response,
)


class Agent(BaseAgent):
    def __init__(
        self,
        tools: Optional[
            Union[Sequence[Union[BaseTool, Callable, dict[str, Any]]], ToolNode]
        ] = None,
        name: Optional[str] = None,
        print_chat_output: bool = True,
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
        )

        self.user_provided_feedback = False

    def build_graph(self):
        """Build the react agent graph."""
        from langgraph.graph import END

        workflow = StateGraph(self.state_schema, config_schema=BaseConfiguration)

        # Add nodes
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("finalize", self.finalize)
        workflow.add_node(
            "user_feedback_on_generated_code", self.user_feedback_on_generated_code
        )
        workflow.add_node("check_code", check_code)
        workflow.add_node(
            "get_relevant_function_documentation",
            get_relevant_function_documentation,
        )

        if not self.part_of_multi_agent:
            workflow.add_node("get_user_input", self.get_user_input)

        # Set entry point
        if self.part_of_multi_agent:
            workflow.set_entry_point("agent")
        else:
            workflow.set_entry_point("get_user_input")
            workflow.add_edge("get_user_input", "agent")

        # Add edges
        workflow.add_edge("get_relevant_function_documentation", "agent")
        workflow.add_edge("tools", "agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                "continue": "user_feedback_on_generated_code",
            },
        )
        workflow.add_conditional_edges(
            "user_feedback_on_generated_code",
            self.direct_after_user_feedback_on_generated_code,
            {
                "agent": "agent",
                "check_code": "check_code",
            },
        )
        workflow.add_conditional_edges(
            "check_code",
            self.direct_after_check_code,
            {
                "get_relevant_function_documentation": "get_relevant_function_documentation",
                "finalize": "finalize",
            },
        )
        if self.part_of_multi_agent:
            workflow.add_edge("finalize", END)
        else:
            workflow.add_edge("finalize", "get_user_input")

        # Compile with memory if standalone
        return workflow.compile()

    def load_model(self, config: RunnableConfig) -> BaseChatModel:
        """
        Load the model from the name specified in the configuration.
        """
        configuration = BaseConfiguration.from_runnable_config(config)
        return self._setup_model(model=configuration.coding_model)

    def get_prompt_from_config(self, config: RunnableConfig) -> str:
        """
        Get the prompt from the configuration.

        Returns:
            A string containing the spesific prompt from the config
        """
        configuration = BaseConfiguration.from_runnable_config(config)
        return configuration.default_coder_prompt

    def call_model(self, state: State, config: RunnableConfig) -> dict:
        """Call the model with the current state."""

        model = self.load_model(config=config)

        configuration = BaseConfiguration.from_runnable_config(config)

        messages = state.messages
        self._validate_chat_history(messages)

        # Add the prompt
        messages_list: List = [SystemMessage(content=configuration.code_prompt)]

        # Add the retrieved context if it exists
        if state.retrieved_context:
            retrieved_context_message = (
                "The following context was retrieved and summarized by a RAG agent. It can be relevant to the code you are about to generate:\n\n"
                + state.retrieved_context
            )
            messages_list.append(HumanMessage(content=retrieved_context_message))
        if state.retrieved_function_documentation:
            retrieved_function_documentation_message = (
                "The following function documentation might be relevant to your code generation:\n\n"
                + state.retrieved_function_documentation
            )
            messages_list.append(
                HumanMessage(content=retrieved_function_documentation_message)
            )

        # Add the state messages
        trimmed_state_messages = self._trim_state_messages(state.messages, model)
        messages_list.extend(trimmed_state_messages)

        # Invoke the model
        response = cast(AIMessage, model.invoke(messages_list, config))

        # Add agent name to the response
        response.name = self.name

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

        if response.content.strip() and self.print_chat_output:
            print_to_console(
                text=response.content.strip(),
                title=self.name,
                border_style=colorscheme.normal,
            )

        code_block = get_code_from_response(response=response.content)

        return {"messages": [response], "code_block": code_block, "error": False}

    def user_feedback_on_generated_code(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)

        # If no human interaction
        if not configuration.human_interaction.generated_code:
            return {}

        code_block = state.code_block
        if code_block.is_empty():
            return {}

        new_code_block, code_updated, user_feedback = code_block, False, ""
        if cli_mode:
            new_code_block, code_updated, user_feedback = (
                cli_response_on_generated_code(code_block)
            )
        else:  # UI mode
            new_code_block, code_updated, user_feedback = response_on_generated_code(
                code_block
            )

        if user_feedback:
            self.user_provided_feedback = True
            return {"messages": [HumanMessage(content=user_feedback)]}
        elif code_updated:
            code_updated_message = (
                "Based on the code you generated, I manually updated it to the following:\n"
                + f"{new_code_block.get_full_code(within_julia_context=True)}"
            )
            return {
                "messages": [HumanMessage(content=code_updated_message)],
                "code_block": new_code_block,
            }

        return {}

    def finalize(self, state: State, config: RunnableConfig):
        if self.part_of_multi_agent:
            final_message = state.code_block.get_full_code(within_julia_context=True)
            return {"messages": [AIMessage(content=final_message)]}
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
    ) -> Literal["get_relevant_function_documentation", "finalize"]:
        if state.error:
            return "get_relevant_function_documentation"
        return "finalize"

    def decide_to_finish(
        self, state: State, config: RunnableConfig
    ) -> Literal["call_model", "end"]:
        return "end"


agent = Agent(
    tools=[
        retrieve_fimbul_tool,
        retrieve_jutuldarcy_tool,
        retrieve_function_signature_tool,
        read_from_file_tool,
        write_to_file_tool,
    ],
    name="Agent",
    print_chat_output=True,
)
graph = agent.graph
