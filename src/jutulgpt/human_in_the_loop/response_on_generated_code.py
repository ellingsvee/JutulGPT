from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt

import jutulgpt.state as state


def response_on_generated_code(
    code_block: state.CodeBlock,
) -> tuple[state.CodeBlock, bool, str]:
    from jutulgpt.utils import get_code_from_response

    # If there is no code to edit, return immediately
    if code_block.is_empty():
        return code_block, False, ""

    # Format the code for display in the UI
    full_code = code_block.get_full_code(within_julia_context=True)

    # Prepare the human-in-the-loop UI request
    request = HumanInterrupt(
        action_request=ActionRequest(
            action="Accept the generated code, or edit it manually. Respond to the agent to suggest changes.",
            args={"Code": full_code},
        ),
        config=HumanInterruptConfig(
            allow_ignore=False,
            allow_accept=True,
            allow_respond=True,
            allow_edit=True,
        ),
    )

    # Wait for the user's response from the UI
    human_response: HumanResponse = interrupt([request])[0]
    response_type = human_response.get("type")

    if response_type == "accept":
        return code_block, False, ""

    elif response_type == "edit":
        args_dics = human_response.get("args", {}).get("args", {})

        # Get the updated code
        full_code = args_dics.get("Code", full_code)

        # Update the code block with the new code
        updated_code_block = get_code_from_response(
            full_code, within_julia_context=True
        )
        return updated_code_block, True, ""

    elif response_type == "respond":
        # return code_block, False, ""
        raise NotImplementedError(
            f"Interrupt value of type {response_type} is yet implemented."
        )
    else:
        raise TypeError(f"Interrupt value of type {response_type} is not supported.")
