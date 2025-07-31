"""This module contains the `generate_response` function which is responsible for generating a response."""

import json
import os
from typing import cast

from langchain_core.messages import AIMessage, HumanMessage, trim_messages
from langchain_core.runnables import RunnableConfig
from rich.console import Console

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.nodes._tools import agent_tools
from jutulgpt.state import State
from jutulgpt.utils import load_chat_model


def generate_response(state: State, config: RunnableConfig, console: Console):
    """Generate a response based on the given state and configuration.

    This function initializes a chat model with tool bindings, formats the system prompt,
    trims the state messages to fit within the model's context window, and invokes the model
    to generate a response. If the state indicates it's the last step and the model still
    wants to use a tool, it returns a message indicating that an answer could not be found.

    Args:
        state (ReactGraphAnnotation): The current state of the react graph.
        config (RunnableConfig): The configuration for running the model.

    Returns:
        dict[str, list[AIMessage]]: A dictionary containing the model's response messages.
    """
    messages = state.messages

    configuration = BaseConfiguration.from_runnable_config(config)

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(configuration.response_model).bind_tools(agent_tools)

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.default_coder_prompt

    trimmedStateMessages = trim_messages(
        messages,
        max_tokens=40000,  # adjust for model's context window minus system & files message
        strategy="last",
        token_counter=model,
        include_system=False,  # Not needed since systemMessage is added separately
        allow_partial=True,
    )

    # Get the model's response
    response = cast(
        AIMessage,
        model.invoke(
            [
                {"role": "system", "content": system_message},
                HumanMessage(content=f"Working directory: {os.getcwd()}"),
                *trimmedStateMessages,
            ],
            config,
        ),
    )

    # CLI
    if response.content.strip():
        print_to_console(
            response.content,
            title="Assistant",
            border_style=colorscheme.normal,
        )

    for tool_call in getattr(response, "tool_calls", []):
        print_to_console(
            tool_call["name"] + ": " + json.dumps(tool_call["args"]),
            title="Tool Call",
            border_style=colorscheme.message,
        )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        ai_message = "Sorry, I could not find an answer to your question in the specified number of steps."
        print_to_console(ai_message, title="Assistant", border_style=colorscheme.normal)
        return {
            "messages": [
                AIMessage(
                    id=response.id,
                    content=ai_message,
                )
            ],
        }
    # Return the model's response as a list to be added to existing messages
    return {
        "messages": [response],
    }
