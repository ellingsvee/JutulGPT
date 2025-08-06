from typing import Any, Callable, Optional, Sequence, Union, cast

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, tool
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.globals import store_retrieved_context
from jutulgpt.multi_agent_system.agents.agent_base import BaseAgent
from jutulgpt.multi_agent_system.agents.coding_agent import coding_graph
from jutulgpt.multi_agent_system.agents.rag_agent import rag_graph
from jutulgpt.state import State
from jutulgpt.tools import read_from_file_tool, write_to_file_tool

# TODO: Possibly move these to a more appropriate place
# rag_graph = RAGAgent().graph
# coding_graph = CodingAgent().graph


class RAGAgentToolInput(BaseModel):
    user_question: str = Field(
        "The user question for the RAG agent to answer.",
    )


@tool("rag_agent", args_schema=RAGAgentToolInput)
def rag_agent_tool(user_question: str) -> str:
    """Call a RAG agent to retrieve relevant information related to the user question. This should be used first to gather context before code generation."""
    response = rag_graph.invoke({"messages": [HumanMessage(content=user_question)]})
    retrieved_content = response["messages"][-1].content

    # WARNING: Bad practice to use global variables, but this is a quick fix for now
    global store_retrieved_context
    store_retrieved_context = retrieved_content

    return retrieved_content


class CodingAgentToolInput(BaseModel):
    user_question: str = Field(
        description="The user question for code generation.",
    )
    use_retrieved_context: bool = Field(
        default=True,
        description="Whether to use previously retrieved context from RAG agent.",
    )


@tool("coding_agent", args_schema=CodingAgentToolInput)
def coding_agent_tool(
    user_question: str,
    use_retrieved_context: bool = True,
) -> str:
    """Call a coding agent for generating Julia code. Use this after retrieving relevant context with the RAG agent."""

    retrieved_context = (
        store_retrieved_context  # Load the retrieved context from the global store
    )

    if use_retrieved_context:
        response = coding_graph.invoke(
            {
                "messages": [HumanMessage(content=user_question)],
                "retrieved_context": retrieved_context,
            }
        )
    else:
        response = coding_graph.invoke(
            {"messages": [HumanMessage(content=user_question)]}
        )

    last_ai_message = response["messages"][-1]
    if last_ai_message.type == "ai":
        # If the last message is an AI message, return its content
        return last_ai_message.content

    text = f"""
No AI response generated. Please check the input or the model.

Last message:
{last_ai_message.content}
"""
    print_to_console(
        text=text.strip(),
        title="Error",
        border_style=colorscheme.error,
    )
    return response["messages"][-1].content


class MultiAgent(BaseAgent):
    def __init__(
        self,
        tools: Optional[
            Union[Sequence[Union[BaseTool, Callable, dict[str, Any]]], ToolNode]
        ] = None,
        name: Optional[str] = None,
    ):
        # Set default empty tools if none provided
        if tools is None:
            tools = []

        # Initialize the base agent
        super().__init__(
            tools=tools,
            name=name or "MultiAgent",
            printed_name="Multi-Agent",
            part_of_multi_agent=False,
            state_schema=State,
        )

    def load_model(self, config: RunnableConfig) -> BaseChatModel:
        """
        Load the model from the name specified in the configuration.
        """
        configuration = BaseConfiguration.from_runnable_config(config)
        return self._setup_model(model=configuration.supervisor_model)

    def get_prompt_from_config(self, config: RunnableConfig) -> str:
        """
        Get the prompt from the configuration.

        Returns:
            A string containing the spesific prompt from the config
        """
        configuration = BaseConfiguration.from_runnable_config(config)
        return configuration.supervisor_prompt

    # Define the node that calls the model
    def call_model(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)
        model = self.load_model(config=config)

        # this is similar to customizing the create_react_agent with 'prompt' parameter, but is more flexible
        system_message = configuration.supervisor_prompt

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

        if response.content.strip():
            print_to_console(
                text=response.content.strip(),
                title="Mutli-Agent",
                border_style=colorscheme.normal,
            )

        # If the response.content contains code, and we use a CLI, ask the user if they want to run it and/or save it to a file
        if cli_mode and response.content.strip():
            from jutulgpt.cli.cli_human_interaction import cli_handle_code_response

            # Ensure we pass a string (response.content could be str or list)
            content_str = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
            cli_handle_code_response(content_str)

        # We return a list, because this will get added to the existing list
        return {"messages": [response]}


multi_agent = MultiAgent(
    tools=[
        rag_agent_tool,
        coding_agent_tool,
        read_from_file_tool,
        write_to_file_tool,
    ]
)
graph = multi_agent.graph
multi_agent.graph.get_graph().draw_mermaid_png(
    output_file_path="./multi_agent_graph.png"
)
