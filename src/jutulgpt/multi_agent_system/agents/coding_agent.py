from __future__ import annotations

from typing import List, Literal, cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from jutulgpt.cli import colorscheme, print_to_console, show_startup_screen
from jutulgpt.cli.cli_human_interaction import (
    cli_response_on_check_code,
    cli_response_on_error,
    cli_response_on_generated_code,
)
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.globals import console

# from jutulgpt.nodes import check_code
from jutulgpt.julia import (
    get_error_message,
    get_function_documentation_from_code,
    get_linting_result,
    run_code,
)
from jutulgpt.nodes.check_code import fix_fimbul_imports, shorter_simulations
from jutulgpt.state import State
from jutulgpt.utils import (
    _get_code_string_from_response,
    get_code_from_response,
    load_chat_model,
    trim_state_messages,
)


class CodingAgent:
    def __init__(
        self, part_of_multi_agent: bool = True, prompt: str = None, tools: List = []
    ):
        self.tools = tools
        self.part_of_multi_agent = part_of_multi_agent
        self.prompt = prompt

        # Generating and plotting the graph
        self.graph = self.build_graph()
        self.graph.get_graph().draw_mermaid_png(output_file_path="./agent_graph.png")

        self.user_provided_feedback = False

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)

        # Add nodes
        workflow.add_node("call_coding_agent", self.call_coding_agent)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node(
            "user_feedback_on_generated_code", self.user_feedback_on_generated_code
        )
        workflow.add_node("check_code", self.check_code)
        workflow.add_node(
            "get_relevant_function_documentation",
            self.get_relevant_function_documentation,
        )
        workflow.add_node("finalize", self.finalize)
        if not self.part_of_multi_agent:
            workflow.add_node("get_user_input", self.get_user_input)

        # Set the entrypoint
        if self.part_of_multi_agent:
            workflow.set_entry_point("get_relevant_function_documentation")
        else:
            workflow.set_entry_point("get_user_input")
            workflow.add_edge("get_user_input", "get_relevant_function_documentation")

        # Edges
        workflow.add_edge("get_relevant_function_documentation", "call_coding_agent")
        workflow.add_edge("tools", "call_coding_agent")
        workflow.add_conditional_edges(
            "call_coding_agent",
            self.check_tool_use,
            {
                "tool_used": "tools",
                "end": "user_feedback_on_generated_code",
            },
        )
        workflow.add_conditional_edges(
            "user_feedback_on_generated_code",
            self.direct_after_user_feedback_on_generated_code,
            {
                "call_coding_agent": "call_coding_agent",
                "check_code": "check_code",
            },
        )
        workflow.add_conditional_edges(
            "check_code",
            self.direct_after_check_code,
            {
                "get_relevant_function_documentation": "get_relevant_function_documentation",
                "finalize": "finalize",
            },
        )

        if self.part_of_multi_agent:
            workflow.add_edge("finalize", END)
        else:
            workflow.add_edge("finalize", "get_user_input")

        return workflow.compile(name="agent")

    def get_user_input(self, state: State, config: RunnableConfig):
        console.print("[bold blue]User Input:[/bold blue] ")
        user_input = console.input("> ")

        # Check for quit command
        if user_input.strip().lower() in ["q"]:
            console.print("[bold red]Goodbye![/bold red]")
            exit(0)

        return {"messages": [HumanMessage(content=user_input)]}

    def call_coding_agent(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)
        model = load_chat_model(configuration.coding_model).bind_tools(self.tools)

        # Add the prompt
        messages_list: List = [
            SystemMessage(
                content=configuration.code_prompt
                if self.prompt is None
                else self.prompt
            )
        ]

        # Add the retrieved context if it exists
        if state.retrieved_context:
            retrieved_context_message = (
                "The following context was retrieved and summarized by a RAG agent. It can be relevant to the code you are about to generate:\n\n"
                + state.retrieved_context
            )
            messages_list.append(HumanMessage(content=retrieved_context_message))
        if state.retrieved_function_documentation:
            retrieved_function_documentation_message = (
                "The following function documentation might be relevant to your code generation:\n\n"
                + state.retrieved_function_documentation
            )
            messages_list.append(
                HumanMessage(content=retrieved_function_documentation_message)
            )

        # Add the state messages
        trimmed_state_messages = trim_state_messages(state.messages, model)
        messages_list.extend(trimmed_state_messages)

        # Invoke the model
        response = cast(
            AIMessage,
            model.invoke(
                messages_list,
                config,
            ),
        )
        code_block = get_code_from_response(response=response.content)

        # Print response if not part of multi-agent
        if response.content.strip() and not self.part_of_multi_agent:
            print_to_console(
                text=response.content.strip(),
                title="Agent",
                border_style=colorscheme.normal,
            )

        return {"messages": [response], "code_block": code_block, "error": False}

    def user_feedback_on_generated_code(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)

        # If no human interaction
        if not configuration.human_interaction.generated_code:
            return {}

        code_block = state.code_block
        if code_block.is_empty():
            return {}

        new_code_block, code_updated, user_feedback = code_block, False, ""
        if cli_mode:
            new_code_block, code_updated, user_feedback = (
                cli_response_on_generated_code(code_block)
            )

        if user_feedback:
            self.user_provided_feedback = True
            return {"messages": [HumanMessage(content=user_feedback)]}
        elif code_updated:
            code_updated_message = (
                "Based on the code you generated, I manually updated it to the following:\n"
                + f"{new_code_block.get_full_code(within_julia_context=True)}"
            )
            return {
                "messages": [HumanMessage(content=code_updated_message)],
                "code_block": new_code_block,
            }

        return {}

    def get_relevant_function_documentation(
        self,
        state: State,
        config: RunnableConfig,
    ):
        if not state.code_block.is_empty():
            return self.get_relevant_function_documentation_from_code(state, config)

        if state.retrieved_context:
            return self.get_relevant_function_documentation_from_retrieved_context(
                state, config
            )

        return {}

    def get_relevant_function_documentation_from_retrieved_context(
        self,
        state: State,
        config: RunnableConfig,
    ):
        retrieved_context = state.retrieved_context

        # Get the code from the retrieved context
        full_code = _get_code_string_from_response(retrieved_context)

        retrieved_function_documentation = get_function_documentation_from_code(
            full_code
        )

        # If any documentation was retrieved, add it ot the state
        if retrieved_function_documentation:
            return {
                "retrieved_function_documentation": retrieved_function_documentation
            }
        return {}

    def get_relevant_function_documentation_from_code(
        self,
        state: State,
        config: RunnableConfig,
    ):
        # TODO: Here we have two more alternatives: Either use a LLM to find relevant functions from the retrieved examples, or use some kind of regex.
        # This can then be passed to the retriever before the first code generation step.

        code_block = state.code_block

        # Try to retrieve the function documentation from the code
        retrieved_function_documentation = get_function_documentation_from_code(
            code_block.get_full_code()
        )

        # If any documentation was retrieved, add it ot the state
        if retrieved_function_documentation:
            return {
                "retrieved_function_documentation": retrieved_function_documentation
            }
        return {}

    def check_code(
        self,
        state: State,
        config: RunnableConfig,
    ):
        configuration = BaseConfiguration.from_runnable_config(config)
        code_block = state.code_block

        if code_block.is_empty():
            return {"error": False}

        check_code_bool = True
        if configuration.human_interaction.code_check:
            check_code_bool = cli_response_on_check_code()

        # Return early if the user chose to ignore the code check
        if not check_code_bool:
            return {"error": False}

        # First fix the use of the Fimbul package
        code_block = fix_fimbul_imports(code_block)

        # Then shorten the code for faster simulations
        full_code = shorter_simulations(code_block.get_full_code())

        # Running the linter
        linting_message, linting_issues_found = self.run_linter(full_code)

        # Running the code
        code_running_message, code_running_issues_found = self.run_code(full_code)

        # If we did not find any issues, we return the final code
        if not linting_issues_found and not code_running_issues_found:
            return {"error": False}

        # If we found issues, we prepare the feedback messages
        feedback_message = (
            "# Code check issues found. Please use these to fix your code:\n"
        )
        if linting_issues_found:
            feedback_message += linting_message + "\n"
        if code_running_issues_found:
            feedback_message += code_running_message

        # Return the feedback messages and and error flag
        return {"messages": [HumanMessage(content=feedback_message)], "error": True}

    def run_linter(self, full_code: str) -> tuple[str, bool]:
        """
        Returns:
            str: String containing the linting issues found in the code. Empty if no issues found.
            bool: True if issues were found, False otherwise.
        """
        linting_result = get_linting_result(full_code)
        if linting_result:
            linting_message = (
                "## Linter issues found:\n"
                + "Linter returned the following issues:\n"
                + linting_result
            )
            return linting_message, True
        return "", False

    def run_code(self, full_code: str) -> tuple[str, bool]:
        """
        Returns:
            str: String containing the code running failed. Empty if the code executed successfully.
            bool: True if issues were found, False otherwise.
        """

        print_to_console(
            text="Running code...",
            title="Code Runner",
            border_style=colorscheme.warning,
        )

        # result = run_string(full_code)
        result = run_code(full_code)

        if result.get("error", False):
            julia_error_message = get_error_message(result)

            print_to_console(
                text=f"Code failed!\n\n{julia_error_message}",
                title="Code Runner",
                border_style=colorscheme.error,
            )

            code_runner_error_message = (
                "## Code runner error:\n"
                + "Running the code generated failed with the following error:\n"
                + julia_error_message
            )
            return code_runner_error_message, True

        print_to_console(
            text=f"Code succeded in {round(result['runtime'], 2)} seconds!",
            title="Code Runner",
            border_style=colorscheme.success,
        )

        return "", False

    def finalize(self, state: State, config: RunnableConfig):
        if self.part_of_multi_agent:
            final_message = state.code_block.get_full_code(within_julia_context=True)
            return {"messages": [AIMessage(content=final_message)]}
        return {}

    def check_tool_use(self, state: State) -> Literal["tool_used", "end"]:
        messages = state.messages
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tool_used"
        else:
            return "end"

    def direct_after_user_feedback_on_generated_code(
        self, state: State
    ) -> Literal["call_coding_agent", "check_code"]:
        if self.user_provided_feedback:
            self.user_provided_feedback = False
            return "call_coding_agent"
        return "check_code"

    def direct_after_check_code(
        self, state: State, config: RunnableConfig
    ) -> Literal["get_relevant_function_documentation", "finalize"]:
        if state.error:
            configuration = BaseConfiguration.from_runnable_config(config)
            try_to_fix_code_bool = True
            if configuration.human_interaction.decide_to_try_to_fix_error and cli_mode:
                try_to_fix_code_bool = cli_response_on_error()
            if try_to_fix_code_bool:
                return "get_relevant_function_documentation"
        return "finalize"

    def decide_to_finish(
        self, state: State, config: RunnableConfig
    ) -> Literal["call_model", "end"]:
        return "end"

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
