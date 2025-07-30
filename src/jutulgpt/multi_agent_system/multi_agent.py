from typing import Annotated, cast

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field
from rich.console import Console

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.human_in_the_loop import modify_rag_query
from jutulgpt.multi_agent_system.agents import CodingAgent, RAGAgent
from jutulgpt.state import State
from jutulgpt.tools import ReadFromFile, WriteToFile
from jutulgpt.utils import load_chat_model

rag_graph = RAGAgent().graph
coding_graph = CodingAgent().graph


class RAGAgentToolInput(BaseModel):
    user_question: str = Field(
        "The user question for the RAG agent to answer.",
    )


class RAGAgentTool(BaseTool):
    name: str = "rag_agent"
    description: str = "Call a RAG agent to retrieve relevant information related to the user question. This should be used first to gather context before code generation."
    args_schema = RAGAgentToolInput

    def _run(
        self, user_question: str, config: Annotated[RunnableConfig, InjectedToolArg]
    ) -> str:
        configuration = BaseConfiguration.from_runnable_config(config)
        if configuration.human_interaction:
            if configuration.cli_mode:
                # CLI mode: use interactive CLI query modification
                from rich.console import Console

                from jutulgpt.cli.cli_utils import cli_modify_rag_query

                console = Console()
                user_question = cli_modify_rag_query(
                    console, user_question, "JutulDarcy"
                )
            else:
                # UI mode: use the original UI-based interaction
                user_question = modify_rag_query(user_question, "JutulDarcy")

        if user_question.strip():
            response = rag_graph.invoke(
                {"messages": [HumanMessage(content=user_question)]}
            )
            retrieved_content = response["messages"][-1].content
        else:
            retrieved_content = "The retrieval was skipped by the user. It is not relevant to the current question."

        return retrieved_content


class CodingAgentToolInput(BaseModel):
    user_question: str = Field(
        description="The user question for code generation.",
    )
    use_retrieved_context: bool = Field(
        default=True,
        description="Whether to use previously retrieved context from RAG agent.",
    )


class CodingAgentTool(BaseTool):
    name: str = "coding_agent"
    description: str = "Call a coding agent for generating Julia code. Use this after retrieving relevant context with the RAG agent."
    args_schema = CodingAgentToolInput

    def _run(
        self,
        user_question: str,
        use_retrieved_context: bool = True,
        config: Annotated[RunnableConfig, InjectedToolArg] | None = None,
        retrieved_context: str = "",
    ) -> str:
        # Prepare the coding request with context
        if retrieved_context and use_retrieved_context:
            coding_prompt = f"""Based on the following retrieved context, please generate Julia code for the user's request.

Retrieved Context:
{retrieved_context}

User Request: {user_question}

Please generate appropriate Julia code using the context above."""
        else:
            coding_prompt = user_question

        response = coding_graph.invoke(
            {"messages": [HumanMessage(content=coding_prompt)]}
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
        self.console = Console()
        self.tools = [RAGAgentTool(), CodingAgentTool(), ReadFromFile(), WriteToFile()]
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)

        # Define the two nodes we will cycle between
        workflow.add_node("user_input", self._get_user_input)
        workflow.add_node("call_model", self.call_model)
        workflow.add_node("tools", self.tool_node)

        # Set the entrypoint as `agent`
        workflow.set_entry_point("user_input")
        workflow.add_edge("user_input", "call_model")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            "call_model",
            self.should_continue,
            {
                "continue": "tools",
                END: "user_input",
            },
        )

        workflow.add_edge("tools", "call_model")

        return workflow.compile(name="supervisor_agent")

    def _get_user_input(self, state: State, config: RunnableConfig) -> State:
        self.console.print("[bold blue]User Input:[/bold blue] ")
        user_input = self.console.input("> ")

        # Check for quit command
        if user_input.strip().lower() in ["q"]:
            self.console.print("[bold red]Goodbye![/bold red]")
            exit(0)

        return {"messages": [HumanMessage(content=user_input)]}

    # Define the node that calls the model
    def call_model(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)
        model = load_chat_model(configuration.response_model).bind_tools(self.tools)

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

    def tool_node(self, state: State, config: RunnableConfig) -> State:
        tools_by_name = {tool.name: tool for tool in self.tools}
        response = []
        last_message = state.messages[-1]
        tool_calls = getattr(last_message, "tool_calls", [])

        retrieved_context = ""

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool = tools_by_name[tool_name]

            try:
                if tool_name == "coding_agent":
                    tool_result = tool._run(
                        **tool_args,
                        config=config,
                        retrieved_context=state.retrieved_context,
                    )
                else:
                    tool_result = tool._run(**tool_args, config=config)
                response.append(
                    ToolMessage(
                        content=tool_result,
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                if tool_name == "rag_agent":
                    retrieved_context += tool_result + "\n"

                title = ""
                if tool_name == "rag_agent":
                    title = "RAG Agent"
                elif tool_name == "coding_agent":
                    title = "Coding Agent"
                else:
                    title = "Agent"

                # if tool_name != "coding_agent":
                #     print_to_console(
                #         console=self.console,
                #         text=tool_result,
                #         title=title,
                #         border_style=colorscheme.normal,
                #     )
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

        if retrieved_context:
            return {"messages": response, "retrieved_context": retrieved_context}
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


multi_agent = MultiAgent()
multi_agent.graph.get_graph().draw_mermaid_png(
    output_file_path="./multi_agent_graph.png"
)
