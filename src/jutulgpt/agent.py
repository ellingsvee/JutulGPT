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
from rich.markdown import Markdown
from rich.panel import Panel
from langgraph.prebuilt import ToolNode


from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.nodes import check_code, generate_response
from jutulgpt.nodes._tools import agent_tools
from jutulgpt.state import State
from jutulgpt.globals import console


class Agent:
    def __init__(self):
        self.tools = agent_tools
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)

        workflow.add_node(
            "generate_response", partial(generate_response, console=console)
        )
        workflow.add_node("check_code", partial(check_code, console=console))
        workflow.add_node("tool_use", ToolNode(agent_tools))

        if cli_mode:
            workflow.set_entry_point("user_input")
            workflow.add_node("user_input", self._get_user_input)
            workflow.add_edge("user_input", "generate_response")
        else:
            workflow.set_entry_point("generate_response")

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
            self.decide_to_finish,
            {
                END: "user_input" if cli_mode else END,
                "generate_response": "generate_response",
            },
        )

        return workflow.compile(name="agent")

    def _get_user_input(self, state: State, config: RunnableConfig) -> State:
        console.print("[bold blue]User Input:[/bold blue] ")
        user_input = console.input("> ")

        # Check for quit command
        if user_input.strip().lower() in ["q"]:
            console.print("[bold red]Goodbye![/bold red]")
            exit(0)

        return {"messages": [HumanMessage(content=user_input)]}

    def _check_tool_use(
        self, state: State, config: RunnableConfig
    ) -> Literal["check_code", "tool_use"]:
        last_message = state.messages[-1]
        if getattr(last_message, "tool_calls", None):
            return "tool_use"
        return "check_code"

    def decide_to_finish(
        self, state: State, config: RunnableConfig
    ) -> Literal["generate_response", END]:
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
            return END
        else:
            return "generate_response"

    def run(self, config: dict = {"cli_mode": True}) -> None:
        """Run the CLI in interactive mode."""
        try:
            # Create configuration with CLI mode enabled
            while True:
                result = self.graph.invoke(
                    {"messages": [AIMessage(content="What can I do for you?")]},
                    config=config,
                )
        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")


agent = Agent()
graph = agent.graph
graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")
