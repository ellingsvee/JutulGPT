from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt

from jutulgpt.configuration import HUMAN_INTERACTION


def check_shortened_code(imports: str, code: str) -> tuple[str, str]:
    """
    The code is shortened before the test run. This interaction allows the user to previev the shoretned code to make sure nothing breaking has happened.
    """
    if HUMAN_INTERACTION:
        interrupt_message = "The code has automatically been shortened for faster runtime and for avoiding potential softlocks. Fix potential errors, or ifnore to run it as is."

        description = interrupt_message

        # Create the human interrupt request
        request = HumanInterrupt(
            action_request=ActionRequest(
                action="Check shortened code",
                args={"imports": imports, "code": code},
            ),
            config=HumanInterruptConfig(
                allow_ignore=True,
                allow_accept=True,
                allow_respond=False,
                allow_edit=False,
            ),
            description=description,
        )

        # Wait for the user's response
        human_response: HumanResponse = interrupt([request])[0]
        response_type = human_response.get("type")

        if response_type == "accept":
            args_dics = human_response.get("args", {}).get("args", {})
            imports = args_dics.get("imports", imports)
            code = args_dics.get("code", code)

        elif human_response.get("type") == "ignore":
            pass
        else:
            raise TypeError(
                f"Interrupt value of type {type(human_response)} is not supported."
            )
    return imports, code
