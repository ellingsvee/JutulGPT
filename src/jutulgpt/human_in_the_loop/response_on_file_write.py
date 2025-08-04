from langgraph.prebuilt.interrupt import (
    ActionRequest,
    HumanInterrupt,
    HumanInterruptConfig,
    HumanResponse,
)
from langgraph.types import interrupt


def response_on_file_write(file_path: str) -> tuple[bool, str]:
    """
    Returns:
        bool: True if user wants to write to file
        str: Potentially a new filename
    """

    # Prepare the human-in-the-loop UI request
    request = HumanInterrupt(
        action_request=ActionRequest(
            action="Agents tries to write to a file, but the filepath already exists. Accept to overwrite, ignore to skip writing, and edit to specify a new path.",
            args={"Filepath": file_path},
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
        return True, file_path

    elif response_type == "edit":
        args_dics = human_response.get("args", {}).get("args", {})

        # Get the updated code
        file_path = args_dics.get("Filepath", file_path)

        return True, file_path

    elif response_type == "ignore":
        return False, file_path
    else:
        raise TypeError(f"Interrupt value of type {response_type} is not supported.")
