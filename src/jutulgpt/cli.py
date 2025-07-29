from __future__ import annotations

import getpass
import json
import logging
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, Sequence, Type, TypeVar

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableConfig, ensure_config
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel


# Setup of the environment and some logging. Not neccessary to touch this.
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv()
_set_env("OPENAI_API_KEY")


class FileReadToolInput(BaseModel):
    file_path: str = Field(
        description="The absolute path to the file to be read.",
    )


class FileReadTool(BaseTool):
    name: str = "file_read"
    description: str = "Reads a file designated by the supplied absolute path and returns its content as a string."
    args_schema = FileReadToolInput

    def _run(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()


class AgentState(BaseModel):
    messages: Annotated[Sequence[BaseMessage], add_messages]


class SimpleAgent:
    def __init__(self, name):
        self.console = Console()
        self.console.print(Panel.fit("[bold green]JutulGPT[/bold green]"))
        self.model = init_chat_model(
            "gpt-4.1-mini",
            model_provider="openai",
            temperature=0.1,
        )
        self.tools = [FileReadTool()]
        self.model = self.model.bind_tools(self.tools)

        workflow = StateGraph(AgentState)
        workflow.add_node("user_input", self._get_user_input)
        workflow.add_node("model_response", self._get_model_response)
        workflow.add_node("tool_use", self._get_tool_use)

        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "model_response")
        workflow.add_conditional_edges(
            "model_response",
            self._check_tool_use,
            {
                "tool_use": "tool_use",
                "user_input": "user_input",
            },
        )
        workflow.add_edge("tool_use", "model_response")

        self.agent = workflow.compile()

    def _get_user_input(self, state: AgentState) -> AgentState:
        self.console.print("[bold blue]User Input:[/bold blue] ")
        user_input = self.console.input("> ")
        return {"messages": [HumanMessage(content=user_input)]}

    def _get_model_response(self, state: AgentState) -> AgentState:
        messages = [
            SystemMessage(
                content=[
                    {
                        "type": "text",
                        "text": "You are a helpful assistant that can read files and answer questions about them.",
                        "cache_control": {
                            "type": "ephemeral",
                        },
                    }
                ]
            ),
            HumanMessage(content=f"Working directory: {os.getcwd()}"),
        ] + state.messages
        response = self.model.invoke(messages)

        if response.content.strip():
            self.console.print(Panel.fit(Markdown(response.content), title="Assistant"))

        for tool_call in getattr(response, "tool_calls", []):
            self.console.print(
                Panel.fit(
                    Markdown(tool_call["name"] + ": " + json.dumps(tool_call["args"])),
                    title="Tool Call",
                )
            )

        return {"messages": [response]}

    def _check_tool_use(self, state: AgentState) -> str:
        last_message = state.messages[-1]
        if getattr(last_message, "tool_calls", None):
            return "tool_use"
        return "user_input"

    def _get_tool_use(self, state: AgentState) -> AgentState:
        tools_by_name = {tool.name: tool for tool in self.tools}
        response = []
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool = tools_by_name[tool_name]

            try:
                tool_result = tool._run(**tool_args)
                response.append(
                    ToolMessage(
                        content=tool_result,
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                self.console.print(
                    Panel.fit(Markdown(tool_result), title="Tool Result")
                )
            except Exception as e:
                response.append(
                    ToolMessage(
                        content="Error: " + str(e),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                self.console.print(
                    Panel.fit(
                        Markdown(str(e)),
                        title="Tool Error",
                        border_style="red",
                    )
                )

        return {"messages": response}

    def run(self) -> str:
        return self.agent.invoke(
            {"messages": [AIMessage(content="What can I do for you?")]}
        )


if __name__ == "__main__":
    agent = SimpleAgent("TestAgent")
    agent.run()
