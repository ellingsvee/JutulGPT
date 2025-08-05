from typing import cast

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field

from jutulgpt.cli import colorscheme, print_to_console, show_startup_screen
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.globals import console, store_retrieved_context
from jutulgpt.multi_agent_system.agents import CodingAgent, RAGAgent
from jutulgpt.nodes import get_user_input
from jutulgpt.state import State
from jutulgpt.tools import read_from_file_tool, write_to_file_tool
from jutulgpt.utils import load_chat_model

# TODO: Possibly move these to a more appropriate place
rag_graph = RAGAgent().graph
coding_graph = CodingAgent().graph


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
        text=text,
        title="Error",
        border_style=colorscheme.error,
    )
    return response["messages"][-1].content


class MultiAgent:
    def __init__(self):
        self.tools = [
            rag_agent_tool,
            coding_agent_tool,
            read_from_file_tool,
            write_to_file_tool,
        ]
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)

        workflow.add_node("call_model", self.call_model)
        workflow.add_node("tools", ToolNode(self.tools))

        # Set the entrypoint as `agent`
        if cli_mode:
            workflow.set_entry_point("user_input")
            workflow.add_node("user_input", get_user_input)
            workflow.add_edge("user_input", "call_model")
        else:
            workflow.set_entry_point("call_model")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            "call_model",
            self.should_continue,
            {
                "continue": "tools",
                END: "user_input" if cli_mode else END,
            },
        )

        workflow.add_edge("tools", "call_model")

        return workflow.compile(name="agent")

    # Define the node that calls the model
    def call_model(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)
        model = load_chat_model(configuration.supervisor_model).bind_tools(self.tools)

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

        if response.content:
            print_to_console(
                text=response.content,
                title="Mutli-Agent",
                border_style=colorscheme.normal,
            )

        # If the response.content contains code, and we use a CLI, ask the user if they want to run it and/or save it to a file
        if cli_mode and response.content:
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

    # Define the conditional edge that determines whether to continue or not
    def should_continue(self, state: State):
        messages = state.messages
        last_message = messages[-1]
        # If there is no function call, then we finish - only AIMessage has tool_calls
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "continue"
        else:
            return END

    def run(self) -> None:
        """Run the CLI in interactive mode."""
        try:
            # Show the startup screen
            show_startup_screen()

            # Create configuration with CLI mode enabled
            config = {}
            while True:
                self.graph.invoke(
                    {"messages": [AIMessage(content="What can I do for you?")]},
                    config=config,
                )
        except KeyboardInterrupt:
            console.print("\n[bold red]Goodbye![/bold red]")


multi_agent = MultiAgent()
graph = multi_agent.graph
multi_agent.graph.get_graph().draw_mermaid_png(
    output_file_path="./multi_agent_graph.png"
)
