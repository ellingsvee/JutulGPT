from __future__ import annotations

from typing import Literal, cast

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.julia import get_function_documentation_from_code, get_linting_result
from jutulgpt.nodes import check_code
from jutulgpt.state import State
from jutulgpt.utils import get_code_from_response, load_chat_model


class CodingAgent:
    def __init__(self):
        self.tools = []
        self.graph = self.build_graph()

    def build_graph(self):
        workflow = StateGraph(State, config_schema=BaseConfiguration)

        # Define the two nodes we will cycle between
        workflow.add_node("call_model", self.call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("check_code", check_code)

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
        model = load_chat_model(configuration.coding_model).bind_tools(self.tools)

        system_message = configuration.code_prompt
        messages_list = [
            {"role": "system", "content": system_message},
            *state.messages,
        ]

        # Get the model's response
        print_to_console(
            text="Generating code...",
            title="Coding agent",
            border_style=colorscheme.warning,
        )
        response = cast(
            AIMessage,
            model.invoke(
                messages_list,
                config,
            ),
        )
        print_to_console(
            text="Code generated!",
            title="Coding agent",
            border_style=colorscheme.success,
        )

        generated_code_block = get_code_from_response(response.content)
        generated_full_code = generated_code_block.get_full_code(
            return_empty_if_no_code=True
        )

        if generated_full_code:
            messages_list.append(response)

            # Run a linter on the generated code
            linting_result = get_linting_result(generated_full_code)
            if linting_result:
                linting_message = f"""
I ran a linter on the code you generated, and it returned the following issues. Please go through them and fix the code accordingly:
{linting_result}
"""
                messages_list.append(HumanMessage(content=linting_message))

                # After the code is generated the first time, we try to retrieve the function documentations
                # WARNING: Now choose to only to the document retrieval if the linter returned issues
                retrieved_function_documentation = get_function_documentation_from_code(
                    generated_full_code
                )

                if retrieved_function_documentation:
                    retrieved_function_documentation_message = f"""
Based on the code you generated, I retrieved the following documentation for the functions you used. Go through it and use it to improve and fix your code:
{retrieved_function_documentation}
"""
                    messages_list.append(
                        HumanMessage(content=retrieved_function_documentation_message)
                    )

                print_to_console(
                    text="Regenerating code...",
                    title="Coding agent",
                    border_style=colorscheme.warning,
                )
                response = cast(
                    AIMessage,
                    model.invoke(
                        messages_list,
                        config,
                    ),
                )
                print_to_console(
                    text="Updated code regenerated!",
                    title="Coding agent",
                    border_style=colorscheme.success,
                )

        # NOTE: Return the regenerate_code to "reset" the state
        return {"messages": [response], "regenerate_code": False}

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
        regenerate_code = state.regenerate_code

        configuration = BaseConfiguration.from_runnable_config(config)

        if regenerate_code:
            return "call_model"
        elif not error or iterations == configuration.max_iterations:
            return END
        else:
            return "call_model"
