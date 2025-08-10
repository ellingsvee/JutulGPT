from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt


def response_on_error() -> tuple[bool, str]:
    # Prepare the human-in-the-loop UI request
    request = HumanInterrupt(
        action_request=ActionRequest(
            action="Code failed. Accept to try to fix it. Ignore to skip code fixing. Respond to give extra feedback to the model",
            args={},
        ),
        config=HumanInterruptConfig(
            allow_ignore=True,
            allow_accept=True,
            allow_respond=True,
            allow_edit=False,
        ),
    )

    # Wait for the user's response from the UI
    human_response: HumanResponse = interrupt([request])[0]
    response_type = human_response.get("type")

    if response_type == "accept":
        return True, ""

    elif response_type == "respond":
        raise NotImplementedError(
            f"Interrupt value of type {response_type} is yet implemented."
        )
        # return True, ""
    elif response_type == "ignore":
        return False, ""
    else:
        raise TypeError(f"Interrupt value of type {response_type} is not supported.")
