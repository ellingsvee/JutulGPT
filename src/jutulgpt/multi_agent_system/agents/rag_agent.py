from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import Annotated, Sequence

from jutulgpt.configuration import BaseConfiguration
from jutulgpt.tools.retrieve import retrieve_fimbul_tool, retrieve_jutuldarcy_tool
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
        self.tools = [retrieve_jutuldarcy_tool, retrieve_fimbul_tool]
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(RAGAgentState, config_schema=BaseConfiguration)

        # Define the two nodes we will cycle between
        workflow.add_node("call_model", self.call_model)
        workflow.add_node("tools", ToolNode(self.tools))

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
