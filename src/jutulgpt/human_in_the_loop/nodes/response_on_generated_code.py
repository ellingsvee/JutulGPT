from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt

from jutulgpt.configuration import Configuration, interactive_environment
from jutulgpt.state import State
from jutulgpt.utils import get_last_code_response


def response_on_generated_code(state: State, config: RunnableConfig):
    """
    Presents the generated code to the user for optional modification before execution or validation.

    If in an interactive environment, displays the generated code in a UI and allows the user to edit it. If the user edits the code,
    a new message is added to the state reflecting the updated code. If the user ignores the prompt, the state is returned unmodified.

    Args:
        state (State): The current agent state, including messages and code.
        config (RunnableConfig): The current configuration for the agent run.

    Returns:
        dict: A dictionary with updated messages if the code was edited, or an empty dict if not.
    """
    if interactive_environment:
        configuration = Configuration.from_runnable_config(config)

        messages = state.messages
        code_block = get_last_code_response(state)
        full_code = code_block.get_full_code(within_julia_context=True)

        description = "The RAG provided you with the following documents. You can modify the content of any of these documents by editing the text in the input boxes below. If you do not want to modify a document, leave the input box empty."
        request = HumanInterrupt(
            action_request=ActionRequest(
                action="Modify the generated code",
                # args={"imports": code_block.imports, "code": code_block.code},
                args={"code": full_code},
            ),
            config=HumanInterruptConfig(
                allow_ignore=True,
                allow_accept=False,
                allow_respond=False,
                allow_edit=True,
            ),
            description=description,
        )

        human_response: HumanResponse = interrupt([request])[0]
        response_type = human_response.get("type")
        if response_type == "edit":
            args_dics = human_response.get("args", {}).get("args", {})

            # Get the updated imports and code
            # imports = args_dics.get("imports", code_block.imports)
            # code = args_dics.get("code", code_block.code)
            full_code = args_dics.get("code", full_code)

            # print(f"Updated imports: {imports}")
            # print(f"Updated code: {code}")

            # Add a new message to the state
            human_message_content = f"""The code was updated by the user. The following is what will be run and checked:
{full_code}
"""

            # Return the updated message.
            # TODO: This should be a message from the user, not an AI message. However, then it does not go correctly to the next node.
            return {"messages": [AIMessage(content=human_message_content)]}

        elif response_type == "ignore":
            pass
        else:
            raise TypeError(
                f"Interrupt value of type {response_type} is not supported."
            )

    # Return the unmodified state. This is always called if not in an interactive environment.
    return {}
