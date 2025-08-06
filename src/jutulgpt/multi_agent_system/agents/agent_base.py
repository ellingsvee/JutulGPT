from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, List, Literal, Optional, Sequence, Union, cast

from langchain_core.language_models import BaseChatModel, LanguageModelLike
from langchain_core.language_models.base import LanguageModelInput
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    trim_messages,
)
from langchain_core.runnables import (
    Runnable,
    RunnableBinding,
    RunnableConfig,
    RunnableSequence,
)
from langchain_core.tools import BaseTool
from langgraph.errors import ErrorCode, create_error_message
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.utils.runnable import RunnableCallable

from jutulgpt.cli import colorscheme, print_to_console, show_startup_screen
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.globals import console
from jutulgpt.state import State
from jutulgpt.utils import get_provider_and_model


class BaseAgent(ABC):
    """
    Abstract base class for all agent types.

    Provides common functionality like model setup, tool processing,
    prompt handling, and utility methods. Child classes must implement
    their own build_graph method to define the specific workflow.
    """

    def __init__(
        self,
        tools: Union[Sequence[Union[BaseTool, Callable, dict[str, Any]]], ToolNode],
        name: Optional[str] = None,
        part_of_multi_agent: bool = False,
        state_schema: Optional[type] = None,
        print_chat_output: bool = True,
    ):
        self.part_of_multi_agent = part_of_multi_agent
        self.name = name or self.__class__.__name__
        self.state_schema = state_schema or State
        self.print_chat_output = print_chat_output

        # Process tools
        if isinstance(tools, ToolNode):
            self.tool_classes = list(tools.tools_by_name.values())
            self.tool_node = tools
        else:
            # Filter out built-in tools (dicts) and create ToolNode with the rest
            self.tool_node = ToolNode([t for t in tools if not isinstance(t, dict)])
            self.tool_classes = list(self.tool_node.tools_by_name.values())

        # Check which tools return direct
        self.should_return_direct = {
            t.name for t in self.tool_classes if t.return_direct
        }

        # Build and compile the graph (implemented by child classes)
        self.graph = self.build_graph()

        # Generate graph visualization
        # self._generate_graph_visualization()

    @abstractmethod
    def load_model(self, config: RunnableConfig) -> BaseChatModel:
        """
        Load the model from the name specified in the configuration.
        """
        pass

    @abstractmethod
    def get_prompt_from_config(self, config: RunnableConfig) -> str:
        """
        Get the prompt from the configuration.

        Returns:
            A string containing the spesific prompt from the config
        """
        pass

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)

        # Define the two nodes we will cycle between
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.tool_node)

        if not self.part_of_multi_agent:
            workflow.add_node("get_user_input", self.get_user_input)

        # Set entry point
        if self.part_of_multi_agent:
            workflow.set_entry_point("agent")
        else:
            workflow.set_entry_point("get_user_input")
            workflow.add_edge("get_user_input", "agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "tools": "tools",
                "continue": END if self.part_of_multi_agent else "get_user_input",
            },
        )

        workflow.add_edge("tools", "agent")

        return workflow.compile(name=self.name)

    def _generate_graph_visualization(self):
        """Generate mermaid visualization of the graph."""
        try:
            filename = f"./{self.name.lower()}_graph.png"
            self.graph.get_graph().draw_mermaid_png(output_file_path=filename)
        except Exception as e:
            # Don't fail if visualization generation fails
            print(f"Warning: Could not generate graph visualization: {e}")

    def _setup_model(self, model: Union[str, LanguageModelLike]) -> BaseChatModel:
        """Setup and bind tools to the model."""
        if isinstance(model, str):
            try:
                from langchain.chat_models import init_chat_model
            except ImportError:
                raise ImportError("Please install langchain to use string model names")

            provider, model_name = get_provider_and_model(model)

            if (
                provider == "ollama" and model_name == "qwen3:14b"
            ):  # WARNING: This is VERY bad practice!
                chat_model = init_chat_model(
                    model_name,
                    model_provider=provider,
                    temperature=0,
                    reasoning=True,
                )
            else:
                chat_model = init_chat_model(
                    model_name, model_provider=provider, temperature=0
                )
            model = cast(BaseChatModel, chat_model)

        # Get the underlying model
        if isinstance(model, RunnableSequence):
            model = next(
                (
                    step
                    for step in model.steps
                    if isinstance(step, (RunnableBinding, BaseChatModel))
                ),
                model,
            )

        if isinstance(model, RunnableBinding):
            model = model.bound

        if not isinstance(model, BaseChatModel):
            raise TypeError(f"Expected model to be a ChatModel, got {type(model)}")

        # Bind tools if needed
        if self._should_bind_tools(model):
            model = model.bind_tools(self.tool_classes)

        return cast(BaseChatModel, model)

    def _should_bind_tools(self, model: BaseChatModel) -> bool:
        """Check if we need to bind tools to the model."""
        if len(self.tool_classes) == 0:
            return False

        if isinstance(model, RunnableBinding):
            if "tools" in model.kwargs:
                bound_tools = model.kwargs["tools"]
                if len(self.tool_classes) != len(bound_tools):
                    raise ValueError(
                        f"Number of tools mismatch. Expected {len(self.tool_classes)}, got {len(bound_tools)}"
                    )
                return False
        return True

    def _get_prompt_runnable(
        self, prompt: Optional[Union[SystemMessage, str]]
    ) -> Runnable:
        """Create a prompt runnable from the prompt."""
        if prompt is None:
            return RunnableCallable(lambda state: state.messages, name="Prompt")
        elif isinstance(prompt, str):
            system_message = SystemMessage(content=prompt)
            return RunnableCallable(
                lambda state: [system_message] + list(state.messages), name="Prompt"
            )
        elif isinstance(prompt, SystemMessage):
            return RunnableCallable(
                lambda state: [prompt] + list(state.messages), name="Prompt"
            )
        else:
            raise ValueError(f"Got unexpected type for prompt: {type(prompt)}")

    def _validate_chat_history(self, messages: Sequence[BaseMessage]) -> None:
        """Validate that all tool calls have corresponding tool messages."""
        all_tool_calls = [
            tool_call
            for message in messages
            if isinstance(message, AIMessage)
            for tool_call in message.tool_calls
        ]
        tool_call_ids_with_results = {
            message.tool_call_id
            for message in messages
            if isinstance(message, ToolMessage)
        }
        tool_calls_without_results = [
            tool_call
            for tool_call in all_tool_calls
            if tool_call["id"] not in tool_call_ids_with_results
        ]
        if tool_calls_without_results:
            error_message = create_error_message(
                message="Found AIMessages with tool_calls that do not have corresponding ToolMessage.",
                error_code=ErrorCode.INVALID_CHAT_HISTORY,
            )
            raise ValueError(error_message)

    def _are_more_steps_needed(self, state: State, response: BaseMessage) -> bool:
        """Check if more steps are needed based on remaining steps and tool calls."""
        has_tool_calls = isinstance(response, AIMessage) and bool(response.tool_calls)
        all_tools_return_direct = (
            all(
                call["name"] in self.should_return_direct
                for call in response.tool_calls
            )
            if isinstance(response, AIMessage) and response.tool_calls
            else False
        )
        remaining_steps = state.remaining_steps
        is_last_step = state.is_last_step

        return (
            (remaining_steps is None and is_last_step and has_tool_calls)
            or (
                remaining_steps is not None
                and remaining_steps < 1
                and all_tools_return_direct
            )
            or (remaining_steps is not None and remaining_steps < 2 and has_tool_calls)
        )

    def _trim_state_messages(
        self,
        messages: Sequence[BaseMessage],
        model: Union[BaseChatModel, Runnable[LanguageModelInput, BaseMessage]],
    ) -> Sequence[BaseMessage]:
        trimmed_state_messages = trim_messages(
            messages,
            max_tokens=40000,  # adjust for model's context window minus system & files message
            strategy="last",
            token_counter=model,
            include_system=False,  # Not needed since systemMessage is added separately
            allow_partial=True,
        )
        return trimmed_state_messages

    def should_continue(self, state: State) -> Literal["tools", "continue"]:
        """Determine whether to continue to tools, end, or get user input."""
        messages = state.messages
        last_message = messages[-1]

        # If the last message has tool calls, go to tools
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "tools"
        else:
            return "continue"

    # Common node functions that can be used by child classes
    def call_model(self, state: State, config: RunnableConfig) -> dict:
        """Call the model with the current state."""

        configuration = BaseConfiguration.from_runnable_config(config)

        # Get the runnable model based on what is specified in the configuration
        model = self.load_model(config=config)
        # prompt_runnable = self._get_prompt_runnable(
        #     self.get_prompt_from_config(config=config)
        # )
        # model_runnable = prompt_runnable | model

        messages = state.messages
        self._validate_chat_history(messages)

        messages_list: List = [SystemMessage(content=configuration.code_prompt)]
        messages_list.extend(messages)
        # Invoke the model
        # response = cast(AIMessage, model_runnable.invoke(state, config))
        response = cast(AIMessage, model.invoke(messages_list, config))

        # Add agent name to the response
        response.name = self.name

        # Check if we need more steps
        # if self._are_more_steps_needed(state, response):
        #     return {
        #         "messages": [
        #             AIMessage(
        #                 id=response.id,
        #                 content="Sorry, need more steps to process this request.",
        #             )
        #         ]
        #     }

        if response.content.strip() and self.print_chat_output:
            print_to_console(
                text=response.content.strip(),
                title=self.name,
                border_style=colorscheme.normal,
            )

        return {"messages": [response]}

    def get_user_input(self, state: State, config: RunnableConfig) -> dict:
        """Get user input for standalone mode."""
        console.print("[bold blue]User Input:[/bold blue] ")
        user_input = console.input("> ")

        # Check for quit command
        if user_input.strip().lower() in ["q", "quit"]:
            console.print("[bold red]Goodbye![/bold red]")
            exit(0)

        return {"messages": [HumanMessage(content=user_input)]}

    # Common utility methods for child classes
    def invoke(
        self, input_data: State, config: Optional[RunnableConfig] = None
    ) -> dict:
        """Invoke the agent (for multi-agent use)."""
        return self.graph.invoke(input_data, config)

    def ainvoke(self, input_data: State, config: Optional[RunnableConfig] = None):
        """Async invoke the agent (for multi-agent use)."""
        return self.graph.ainvoke(input_data, config)

    def run(self) -> None:
        """Run the agent in interactive mode (standalone only)."""
        if self.part_of_multi_agent:
            raise ValueError("Cannot run standalone mode when part_of_multi_agent=True")

        try:
            show_startup_screen()

            # Create configuration
            config = RunnableConfig(configurable={})

            # Create initial state conforming to the state schema
            initial_state = {
                "messages": [],  # Start with empty messages, user input will add the first message
                "remaining_steps": 25,
                "is_last_step": False,
            }

            # The graph will handle the looping internally
            self.graph.invoke(initial_state, config=config)

        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")
