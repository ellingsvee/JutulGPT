"""This module contains the `generate_response` function which is responsible for generating a response."""

from os import error
from typing import cast

from langchain_core.messages import AIMessage, HumanMessage, trim_messages
from langchain_core.runnables import RunnableConfig

from jutulgpt.configuration import Configuration
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.utils import load_chat_model


def generate_response(state: State, config: RunnableConfig):
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
    error = state.error
    error_message = state.error_message

    configuration = Configuration.from_runnable_config(config)

    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(configuration.model).bind_tools(tools)

    # If there was an error in the previous step, add this to the messages.
    error_message_list = []
    if error:
        error_message_list = [
            HumanMessage(
                content=f"The code from you previous response failed with the following error: {error_message}.\n\nFix the error to provide runnable code."
            ),
        ]

    # Format the system prompt. Customize this to change the agent's behavior.
    system_message = configuration.system_prompt

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
            [{"role": "system", "content": system_message}, *trimmedStateMessages],
            config,
        ),
    )

    # Handle the case when it's the last step and the model still wants to use a tool
    if state.is_last_step and response.tool_calls:
        return {
            "messages": error_message_list
            + [
                AIMessage(
                    id=response.id,
                    content="Sorry, I could not find an answer to your question in the specified number of steps.",
                )
            ],
        }

    # Return the model's response as a list to be added to existing messages
    return {"messages": error_message_list + [response]}
