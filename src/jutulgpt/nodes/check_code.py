"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

import re
from typing import cast

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
from langchain_core.runnables import RunnableConfig

from jutulgpt.configuration import Configuration, check_code_bool
from jutulgpt.julia_interface import (
    get_code_from_response,
    get_error_message,
    run_string,
)
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.utils import load_chat_model


def check_code(state: State, config: RunnableConfig):
    configuration = Configuration.from_runnable_config(config)

    if check_code_bool:
        # TODO: Double check that this retrieves the correct result
        last_message = state.messages[-1]
        if last_message.type == "ai":
            last_message_content = last_message.content
        else:
            last_message_content = ""
        code_block = get_code_from_response(last_message_content)

        imports = code_block.imports
        code = code_block.code
        code = _shorter_simulations(
            code
        )  # If the code contains simulations, replace them with shorter ones

        result = run_string(imports)
        if result["error"]:
            julia_error_message = get_error_message(result)
            error_message = f"Failure in import test:\n{julia_error_message}"

            return {
                "error": True,
                "error_message": error_message,
                "iterations": state.iterations + 1,
            }

        full_code = imports + "\n" + code
        result = run_string(full_code)
        if result["error"]:
            julia_error_message = get_error_message(result)
            error_message = f"Failure in code execution test:\n{julia_error_message}"
            return {
                "error": True,
                "error_message": error_message,
                "iterations": state.iterations + 1,
            }

    return {"error": False, "iterations": state.iterations + 1}


def shorter_simulations(code: str) -> str:
    """
    For each simulation function, append '[1:1]' to the first argument of the function call.
    E.g., sim_func_1(foo, bar) -> sim_func_1(foo[1:1], bar)
    """
    simulation_functions = []  # TODO: Add the names of the actual simulation functions here

    for func in simulation_functions:
        # Match the function call and capture the first argument
        pattern = rf"({func}\s*\()\s*([^,)\s]+)(.*?\))"

        def replacer(match):
            before = match.group(1)
            first_arg = match.group(2)
            after = match.group(3)
            return f"{before}{first_arg}[1:1]{after}"

        code = re.sub(pattern, replacer, code, flags=re.DOTALL)

    return code
