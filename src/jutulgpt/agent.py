from __future__ import annotations

import getpass
import os
from functools import partial
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.nodes import check_code, generate_response
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.tools.retrieve import RetrieveJutulDarcyTool


def decide_to_finish(
    state: State, config: RunnableConfig
) -> Literal["generate_response", "user_input"]:
    """
    Determines whether to finish.

    Args:
        state (dict): The current graph state

    Returns:
        str: Next node to call
    """
    error = state.error
    iterations = state.iterations

    configuration = BaseConfiguration.from_runnable_config(config)

    if not error or iterations == configuration.max_iterations:
        return "user_input"
    else:
        return "generate_response"


class JutulGPT:
    def __init__(self):
        self.console = Console()
        # self.console.print(
        #     Panel.fit(
        #         "[bold green]Welcome to JutulGPT. (Type 'q' to quit)[/bold green]"
        #     )
        # )
        self.tools = tools
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)
        workflow.add_node("user_input", self._get_user_input)
        workflow.add_node(
            "generate_response", partial(generate_response, console=self.console)
        )
        workflow.add_node("check_code", partial(check_code, console=self.console))

        # workflow.add_node("model_response", self._get_model_response)
        workflow.add_node("tool_use", self._get_tool_use)

        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self._check_tool_use,
            {
                "tool_use": "tool_use",
                "check_code": "check_code",
            },
        )
        workflow.add_edge("tool_use", "generate_response")

        workflow.add_conditional_edges(
            "check_code",
            decide_to_finish,
            {
                "user_input": "user_input",
                "generate_response": "generate_response",
            },
        )

        return workflow.compile(name="agent")

    def _get_user_input(self, state: State, config: RunnableConfig) -> State:
        self.console.print("[bold blue]User Input:[/bold blue] ")
        user_input = self.console.input("> ")

        # Check for quit command
        if user_input.strip().lower() in ["q"]:
            self.console.print("[bold red]Goodbye![/bold red]")
            exit(0)

        return {"messages": [HumanMessage(content=user_input)]}

    def _check_tool_use(
        self, state: State, config: RunnableConfig
    ) -> Literal["check_code", "tool_use"]:
        last_message = state.messages[-1]
        if getattr(last_message, "tool_calls", None):
            return "tool_use"
        return "check_code"

    def _get_tool_use(self, state: State, config: RunnableConfig) -> State:
        tools_by_name = {tool.name: tool for tool in self.tools}
        response = []
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool = tools_by_name[tool_name]

            try:
                tool_result = tool._run(**tool_args, config=config)
                response.append(
                    ToolMessage(
                        content=tool_result,
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                print_to_console(
                    text=tool_result,
                    title="Tool Result",
                    border_style=colorscheme.normal,
                )
            except Exception as e:
                response.append(
                    ToolMessage(
                        content="Error: " + str(e),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                print_to_console(
                    text=str(e),
                    title="Tool Error",
                    border_style=colorscheme.error,
                )

        return {"messages": response}

    def run(self) -> None:
        """Run the CLI in interactive mode."""
        try:
            # Create configuration with CLI mode enabled
            config = {
                "cli_mode": True,
                # "embedding_model": "ollama/nomic-embed-text",
                # "response_model": "ollama/qwen3:14b",
            }
            while True:
                result = self.graph.invoke(
                    {"messages": [AIMessage(content="What can I do for you?")]},
                    config=config,
                )
        except KeyboardInterrupt:
            self.console.print("\n[bold red]Goodbye![/bold red]")


agent = JutulGPT()
graph = agent.graph
graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
