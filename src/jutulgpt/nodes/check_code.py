"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

from typing import cast

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
from langchain_core.runnables import RunnableConfig

from jutulgpt.configuration import Configuration
from jutulgpt.julia_interface import (
    get_code_from_response,
    get_error_message,
    run_string,
)
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.utils import load_chat_model


def check_code(state: State, config: RunnableConfig) -> State:
    configuration = Configuration.from_runnable_config(config)

    # TODO: Double check that this retrieves the correct result
    messages = state.messages
    last_message = messages[-1].content
    code_block = get_code_from_response(last_message)

    imports = code_block.imports
    code = code_block.code

    result = run_string(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = f"Your solution failed the import test:\n{julia_error_message}"
        response = cast(
            HumanMessage,  # Maybe HumanMessage?
            error_message,
        )

        # messages.append(HumanMessage(content=error_message))
        return {
            "messages": [response],
            "error": True,
            "iterations": state.iterations + 1,
        }

    full_code = imports + "\n" + code
    result = run_string(full_code)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = (
            f"Your solution failed the code execution test:\n{julia_error_message}"
        )
        response = cast(
            HumanMessage,  # Maybe HumanMessage?
            error_message,
        )
        return {
            "messages": [response],
            "error": True,
            "iterations": state.iterations + 1,
        }

    return {"error": False, "iterations": state.iterations + 1}
