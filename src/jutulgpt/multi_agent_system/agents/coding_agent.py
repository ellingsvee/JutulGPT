from __future__ import annotations

from functools import partial
from typing import Literal, cast

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.globals import console
from jutulgpt.nodes import check_code
from jutulgpt.state import State
from jutulgpt.tools import RetrieveFunctionSignatureTool
from jutulgpt.utils import load_chat_model


class CodingAgent:
    def __init__(self):
        self.tools = [RetrieveFunctionSignatureTool()]
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)

        # Define the two nodes we will cycle between
        workflow.add_node("call_model", self.call_model)
        workflow.add_node("tools", self.tool_node)
        workflow.add_node("check_code", partial(check_code, console=console))

        # Set the entrypoint as `agent`
        workflow.set_entry_point("call_model")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            "call_model",
            self.should_continue,
            {
                "continue": "tools",
                END: "check_code",
            },
        )

        workflow.add_edge("tools", "call_model")

        workflow.add_conditional_edges(
            "check_code",
            self.decide_to_finish,
            {
                END: END,
                "call_model": "call_model",
            },
        )

        return workflow.compile(name="coding_agent")

    # Define the node that calls the model
    def call_model(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)
        model = load_chat_model(configuration.response_model).bind_tools(self.tools)

        system_message = configuration.code_prompt

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

        # print_to_console(
        #     text=response.content,
        #     title="Coding Agent",
        #     border_style=colorscheme.normal,
        # )

        # We return a list, because this will get added to the existing list
        return {"messages": [response]}

    # Define the conditional edge that determines whether to continue or not
    def should_continue(self, state: State):
        messages = state.messages
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return END
        # Otherwise if there is, we continue
        else:
            return "continue"

    def tool_node(self, state: State, config: RunnableConfig) -> State:
        tools_by_name = {tool.name: tool for tool in self.tools}
        response = []
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool = tools_by_name[tool_name]

            print(f"CODING AGENT CALLS TOOL!!!: {tool_name}")

            try:
                tool_result = tool._run(**tool_args, config=config)
                response.append(
                    ToolMessage(
                        content=tool_result,
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
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

    def decide_to_finish(
        self, state: State, config: RunnableConfig
    ) -> Literal["call_model", END]:
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
            return "call_model"
