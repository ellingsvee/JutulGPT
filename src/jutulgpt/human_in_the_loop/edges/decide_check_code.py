from typing import Literal

from langgraph.graph import END
from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt

from jutulgpt.configuration import INTERACTIVE_ENVIRONMENT
from jutulgpt.state import State
from jutulgpt.utils import get_last_code_response


def decide_check_code(
    state: State,
) -> Literal["check_code", END]:
    """
    Ask the user whether to check the generated code or proceed to the end of the workflow.

    If in an interactive environment and code is present, prompts the user to decide if the code should be checked (executed and validated)
    or if the agent should finish. If not in an interactive environment, defaults to checking the code.

    Args:
        state (State): The current agent state, including messages and code.
        config (RunnableConfig): The current configuration for the agent run.

    Returns:
        Command[Literal["check_code", END]]: A command indicating the next node to execute ("check_code" or END).
    """
    print("Inside decide_check_code")

    if INTERACTIVE_ENVIRONMENT:
        # Only give the option is there are any code to check.
        code_block = get_last_code_response(state)
        if code_block.imports != "" or code_block.code != "":
            interrupt_message = "Do you want to check the code before proceeding? If you accept, the agent will run the code and try to fix potential errors. If you ignore, the agent will finish."

            description = (
                "Review the generated code and decide if it should be checked."
                + "If you accept, the agent will run the code and try to fix potential errors. "
                + "If you ignore, the agent will finish."
            )

            request = HumanInterrupt(
                action_request=ActionRequest(
                    action="Check code?",
                    args={"code": interrupt_message},
                ),
                config=HumanInterruptConfig(
                    allow_ignore=True,
                    allow_accept=True,
                    allow_respond=False,
                    allow_edit=False,
                ),
                description=description,
            )

            human_response: HumanResponse = interrupt([request])[0]
            response_type = human_response.get("type")

            if response_type == "accept":
                return "check_code"
            elif human_response.get("type") == "ignore":
                return END
            else:
                raise TypeError(
                    f"Interrupt value of type {type(human_response)} is not supported."
                )
        else:
            # Go to end if no code has been generated.
            return END
    # Go to check_code if not in an interactive environment
    return "check_code"
