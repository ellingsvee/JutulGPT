from __future__ import annotations

import os
import re
import subprocess
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
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
from langchain_core.tools import BaseTool, tool
from langgraph.errors import ErrorCode, create_error_message
from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_node import ToolNode
from langgraph.utils.runnable import RunnableCallable

from jutulgpt.cli import (
    colorscheme,
    print_to_console,
    show_startup_screen,
    stream_to_console,
)
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
        printed_name: Optional[str] = "",
        state_schema: Optional[type] = None,
        print_chat_output: bool = True,
        filename: Optional[str] = None,
    ):
        if name is not None and (" " in name or not name):
            raise ValueError("Agent name must not be empty or contain spaces.")

        self.name = name or self.__class__.__name__
        self.printed_name = printed_name
        self.state_schema = state_schema or State
        self.print_chat_output = print_chat_output

        # Setting the base directory for file operations
        self.base_directory = os.getcwd()
        self.filename = filename if filename else "temp_julia_file"

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

    @abstractmethod
    def build_graph(self) -> Any:
        """
        Build the state graph for the agent.

        This method should be implemented by child classes to define
        the specific workflow of the agent.
        """
        pass

    def _get_chat_model(self, model: Union[str, LanguageModelLike]) -> BaseChatModel:
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
                    streaming=True,
                )
            else:
                chat_model = init_chat_model(
                    model_name,
                    model_provider=provider,
                    temperature=0,
                    streaming=True,
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
        # if self._should_bind_tools(model):
        #     model = model.bind_tools(self.tool_classes)

        return cast(BaseChatModel, model)

    def load_model(
        self, model: Union[str, LanguageModelLike], tool_classes: list
    ) -> BaseChatModel:
        """Load the model from the name specified in the configuration."""
        chat_model = self._get_chat_model(model)
        if tool_classes:
            if self._should_bind_tools(chat_model):
                chat_model = chat_model.bind_tools(tool_classes)
        return cast(BaseChatModel, chat_model)

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

    def invoke_model(
        self,
        prompt: str,
        model: BaseChatModel,
        state: State,
        config: RunnableConfig,
    ) -> AIMessage:
        """Invoke the model with the given prompt and state."""
        messages_list: List = [SystemMessage(content=prompt)]
        trimmed_state_messages = self._trim_state_messages(state.messages, model)
        messages_list.extend(trimmed_state_messages)

        # Invoke the model
        if self.print_chat_output:
            chat_response = stream_to_console(
                llm=model,
                message_list=messages_list,
                config=config,
                title=self.printed_name,
                border_style=colorscheme.normal,
            )
            response = cast(AIMessage, chat_response)
        else:
            response = cast(AIMessage, model.invoke(messages_list, config))

        # Add agent name to the response
        response.name = self.name

        return response

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
    @abstractmethod
    def call_model(self, state: State, config: RunnableConfig) -> dict:
        """Call the model with the current state."""
        pass

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

    def _create_julia_workspace(self) -> str:
        """
        Create a simple workspace with a single Julia file.

        Returns:
            str: Path to the created Julia file
        """

        # Simple sanitization
        safe_task_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", self.filename.lower())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        workspace_dir = Path(self.base_directory) / "jutulgpt_workspaces"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        julia_file = workspace_dir / f"{safe_task_name}_{timestamp}.jl"

        print_to_console(
            text=f"Creating Julia workspace for task '{self.filename}' at {julia_file}",
            title="Tool: Create Julia Workspace",
            border_style=colorscheme.message,
        )

        try:
            with open(julia_file, "w") as f:
                f.write(f"# {self.filename}\n")
                f.write(
                    f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

            return str(julia_file)

        except Exception as e:
            return f"ERROR: Failed to create workspace: {str(e)}"

    def write_julia_code_to_file(self, code: str, append: bool = False) -> str:
        """
        Write Julia code to a file.

        Args:
            code: The Julia code to write
            file_path: Path to the Julia file
            append: Whether to append to existing file or overwrite

        Returns:
            str: Confirmation message or error
        """
        print_to_console(
            text=f"Writing Julia code to {self.filename} (append={append})",
            title="Tool: Write Julia Code to File",
            border_style=colorscheme.message,
        )

        try:
            mode = "a" if append else "w"
            with open(self.filename, mode) as f:
                if append:
                    f.write("\n")
                f.write(code)
                if not code.endswith("\n"):
                    f.write("\n")

            action = "appended to" if append else "written to"
            return f"Successfully {action} {self.filename}"

        except Exception as e:
            return f"ERROR: Failed to write to file: {str(e)}"

    def execute_julia_file(self) -> str:
        """
        Execute a Julia file and return the output.

        Args:
            file_path: Path to the Julia file to execute

        Returns:
            str: Execution output and exit code
        """
        print_to_console(
            text=f"Executing Julia file: {self.filename}",
            title="Tool: Execute Julia File",
            border_style=colorscheme.warning,
        )
        try:
            if not os.path.exists(self.filename):
                return f"ERROR: File {self.filename} does not exist"

            result = subprocess.run(
                ["julia", self.filename], capture_output=True, text=True, timeout=30
            )

            output = f"=== Execution of {self.filename} ===\n"

            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"

            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"

            output += f"EXIT CODE: {result.returncode}\n"

            print_to_console(
                text=output.strip(),
                title="Execution Result",
                border_style=colorscheme.success
                if result.returncode == 0
                else colorscheme.error,
            )

            return output

        except subprocess.TimeoutExpired:
            return f"ERROR: Execution of {self.filename} timed out after 30 seconds"
        except Exception as e:
            return f"ERROR: Failed to execute {self.filename}: {str(e)}"

    def run(self) -> None:
        """Run the agent in interactive mode (standalone only)."""
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

            _ = self._create_julia_workspace()

            # The graph will handle the looping internally
            self.graph.invoke(initial_state, config=config)

        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")
