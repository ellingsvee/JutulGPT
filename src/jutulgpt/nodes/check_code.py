"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

from typing import cast

from langchain_core.messages import AIMessage, trim_messages
from langchain_core.runnables import RunnableConfig

from jutulgpt.configuration import Configuration
from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.utils import load_chat_model


def check_code(state: State, config: RunnableConfig) -> dict[str, list[AIMessage]]:
    configuration = Configuration.from_runnable_config(config)

    messages = state.messages
    prefix = structured_resonse.prefix
    imports = structured_resonse.imports
    code = structured_resonse.code

    result = run_string(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = f"Your solution failed the import test:\n{julia_error_message}"

        # messages.append(HumanMessage(content=error_message))
        # return State(
        #     messages=messages,
        #     structured_response=structured_resonse,
        #     error=True,
        #     **state_to_dict(
        #         state, remove_keys=["messages", "structured_response", "error"]
        #     ),
        # )

    full_code = imports + "\n" + code
    result = run_string(full_code)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = (
            f"Your solution failed the code execution test:\n{julia_error_message}"
        )
        # logger.info(
        #     f"""
        #     Code execution failed.
        #     Code that failed: {full_code}
        #     {julia_error_message}
        #     """
        # )
        # messages.append(HumanMessage(content=error_message))
        # return State(
        #     messages=messages,
        #     structured_response=structured_resonse,
        #     error=True,
        #     **state_to_dict(
        #         state, remove_keys=["messages", "structured_response", "error"]
        #     ),
        # )
        return state

    # return State(
    #     messages=messages,
    #     structured_response=structured_resonse,
    #     error=False,
    #     **state_to_dict(
    #         state, remove_keys=["messages", "structured_response", "error"]
    #     ),
    # )
    return state
