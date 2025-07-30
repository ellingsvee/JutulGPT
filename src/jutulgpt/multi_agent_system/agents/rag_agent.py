from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from langchain_core.messages import AIMessage, AnyMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph, add_messages
from rich.console import Console
from typing_extensions import Annotated, Sequence

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.state import State
from jutulgpt.tools.retrieve import RetrieveFimbulTool, RetrieveJutulDarcyTool
from jutulgpt.utils import load_chat_model


@dataclass
class RAGAgentState:
    """
    Base input state for the agent, representing the evolving conversation and tool interaction history.

    - messages: List of all messages exchanged so far (user, AI, tool, etc.).
      The `add_messages` annotation ensures new messages are merged by ID, so the state is append-only unless a message is replaced.
    """

    messages: Annotated[Sequence[AnyMessage], add_messages] = field(
        default_factory=list
    )


class RAGAgent:
    def __init__(self):
        self.console = Console()
        self.tools = [RetrieveJutulDarcyTool(), RetrieveFimbulTool()]
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(RAGAgentState, config_schema=BaseConfiguration)

        # Define the two nodes we will cycle between
        workflow.add_node("call_model", self.call_model)
        workflow.add_node("tools", self.tool_node)

        # Set the entrypoint as `agent`
        workflow.set_entry_point("call_model")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            "call_model",
            self.should_continue,
            {
                "continue": "tools",
                END: END,
            },
        )

        workflow.add_edge("tools", "call_model")

        return workflow.compile(name="rag_agent")

    # Define the node that calls the model
    def call_model(
        self,
        state: RAGAgentState,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)
        model = load_chat_model(configuration.response_model).bind_tools(self.tools)

        # this is similar to customizing the create_react_agent with 'prompt' parameter, but is more flexible
        system_message = configuration.rag_prompt

        # Get the model's response
        response = cast(
            AIMessage,
            model.invoke(
                [
                    {"role": "system", "content": system_message},
                    *state.messages,
                ],
                config,
            ),
        )
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    # Define the conditional edge that determines whether to continue or not
    def should_continue(self, state: RAGAgentState):
        messages = state.messages
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return END
        # Otherwise if there is, we continue
        else:
            return "continue"

    def tool_node(self, state: RAGAgentState, config: RunnableConfig) -> State:
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
                # print_to_console(
                #     console=self.console,
                #     text=tool_result,
                #     title="Tool Result",
                #     border_style=colorscheme.normal,
                # )
            except Exception as e:
                response.append(
                    ToolMessage(
                        content="Error: " + str(e),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                print_to_console(
                    console=self.console,
                    text=str(e),
                    title="Tool Error",
                    border_style=colorscheme.error,
                )

        return {"messages": response}
