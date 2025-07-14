"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

import re
from typing import List, cast

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)
from langchain_core.runnables import RunnableConfig

from jutulgpt.configuration import Configuration, static_config
from jutulgpt.julia_interface import (
    get_code_from_response,
    get_error_message,
    get_last_code_response,
    run_string,
    run_string_line_by_line,
)
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.utils import load_chat_model


def check_code(state: State, config: RunnableConfig):
    configuration = Configuration.from_runnable_config(config)

    code_block = get_last_code_response(state)

    imports = code_block.imports
    code = code_block.code
    code = shorter_simulations(
        code
    )  # If the code contains simulations, replace them with shorter ones

    def gen_error_message_string(
        test_type: str, code_line: str, julia_error_message: str
    ) -> str:
        error_message = f"""
        Failure in {test_type}. The line `{code_line}` failed with the following Julia error message:
        {julia_error_message}
        """
        return error_message

    result = run_string_line_by_line(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = gen_error_message_string(
            "import test", result["line"], julia_error_message
        )

        return {
            "error": True,
            "error_message": error_message,
            "iterations": state.iterations + 1,
        }

    full_code = imports + "\n" + code
    result = run_string_line_by_line(full_code)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = gen_error_message_string(
            "code execution test", result["line"], julia_error_message
        )
        return {
            "error": True,
            "error_message": error_message,
            "iterations": state.iterations + 1,
        }

    return {"error": False, "iterations": state.iterations + 1}


def _shorten_first_argument(code: str, simulation_functions: List[str]) -> str:
    """
    For each simulation function, append '[1:1]' to the first argument of the function call.
    E.g., sim_func_1(foo, bar) -> sim_func_1(foo[1:1], bar)
    """

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


def _replace_case(code: str, case_name: str, simulation_functions: List[str]) -> str:
    """
    Replacing the 'case' with 'case[1:1]'.
    """
    for func in simulation_functions:
        # Match 'case' as a whole word in the argument list
        pattern = rf"({func}\s*\(.*?)(\b{case_name}\b)(.*?\))"

        def replacer(match):
            before = match.group(1)
            after = match.group(3)
            return f"{before}{case_name}[1:1]{after}"

        code = re.sub(pattern, replacer, code, flags=re.DOTALL)
    return code


def shorter_simulations(code: str) -> str:
    """
    In the case when some simulation is called, this function replaces it with a shorter simulation.
    """
    simulation_functions = [
        "simulate_reservoir",
    ]
    original_code = code

    code = _replace_case(
        code=code, case_name="case", simulation_functions=simulation_functions
    )
    code = _replace_case(
        code=code, case_name="dt", simulation_functions=simulation_functions
    )

    if original_code == code:
        # WARNING: If the previous functions have not changed the code, it might inidate that some other name is used. However, this might we a weird assumption?
        code = _shorten_first_argument(
            code=code, simulation_functions=simulation_functions
        )

    print(f"Shortened code:\n{code}")

    return code
