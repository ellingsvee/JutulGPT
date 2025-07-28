from typing import List

from langchain_core.messages import AIMessage
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt

from jutulgpt.configuration import HUMAN_INTERACTION
from jutulgpt.state import CodeBlock
from jutulgpt.utils import get_code_from_response


def response_on_check_code(
    code_block: CodeBlock,
) -> tuple[CodeBlock, bool, List[AIMessage]]:
    """
    Human interaction to potentially modeify the code, or choose to not accept it.

    Args:
        CodeBlock: The code block to potentially modify or accept.

    Returns:
        CodeBlock: The potentially modified code block.
        bool: Whether or not to check the code (True) or ignore it (False).
        List[AIMessage]: A list of AI messages to be added to the state. Only non-empty when the user modifies the code.
    """
    # If there is no code to edit, return immediately
    if not code_block.imports and not code_block.code:
        return code_block, False, []

    if not HUMAN_INTERACTION:
        return code_block, True, []

    # Format the code for display in the UI
    full_code = code_block.get_full_code(within_julia_context=True)

    # Prepare the human-in-the-loop UI request
    request = HumanInterrupt(
        action_request=ActionRequest(
            action="Accept or modify the generated code to check it. Ignore to not check it.",
            args={"Code": full_code},
        ),
        config=HumanInterruptConfig(
            allow_ignore=True,
            allow_accept=True,
            allow_respond=False,
            allow_edit=True,
        ),
    )

    # Wait for the user's response from the UI
    human_response: HumanResponse = interrupt([request])[0]
    response_type = human_response.get("type")

    if response_type == "accept":
        return code_block, True, []

    elif response_type == "edit":
        args_dics = human_response.get("args", {}).get("args", {})

        # Get the updated code
        full_code = args_dics.get("Code", full_code)

        # Add a new message to the state reflecting the user's update
        message_content = f"""The code was updated by the user. The following is what will be run and checked:
{full_code}
"""

        # Update the code block with the new code
        updated_code_block = get_code_from_response(full_code)

        # Return the updated message.
        # TODO: This should be a message from the user, not an AI message. However, then it does not go correctly to the next node.
        # return {"messages": [AIMessage(content=message_content)]}
        return updated_code_block, True, [AIMessage(content=message_content)]

    elif response_type == "ignore":
        return code_block, False, []
    else:
        raise TypeError(f"Interrupt value of type {response_type} is not supported.")
