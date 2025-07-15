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
from langgraph.config import get_stream_writer

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
from jutulgpt.utils import load_chat_model, split_code_into_lines


def check_code(state: State, config: RunnableConfig):
    # writer = get_stream_writer()

    # writer(f"Running code. Please wait...")

    print("Running code, please wait...")
    code_block = get_last_code_response(state)
    imports = code_block.imports
    code = code_block.code
    imports = shorter_simulations(imports)
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
        print(f"check_code: {error_message}")
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
        print(f"check_code: {error_message}")
        return {
            "error": True,
            "error_message": error_message,
            "iterations": state.iterations + 1,
        }

    print("Code executed successfully.")

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


def _remove_plotting(code: str) -> str:
    """
    Remove GLMakie usage and plotting code from Julia code blocks.
    F.ex:
    - Removes 'using GLMakie' or 'using ... GLMakie ...' from using statements.
    - Removes lines that define or use 'fig', 'ax', or call 'lines!'.
    - Removes lines that are just 'fig' (returning the figure).
    """
    # TODO: This is a very naive implementation, it should be improved.
    remove_functions = [
        "fig",
        "plt",
        "ax",
        "scatter",
        "Colorbar",
        "Axis",
        "lines",
        "plot_reservoir",
        "plot_well_results",
        "plot_reservoir_measurables",
        "plot_reservoir_simulation_result",
        "plot_well!",
        "myplot",
        "plot_cell_data",
        "plot_mesh_edges",
        "plot_mesh",
        "plot_co2_inventory",
    ]

    # lines = code.splitlines()
    lines = split_code_into_lines(code)
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # Remove 'using GLMakie' or 'using ... GLMakie ...'
        if stripped.startswith("using"):
            # Remove 'GLMakie' from the using statement
            # Handles cases like: using JutulDarcy, GLMakie, Jutul;
            # and: using GLMakie
            line = re.sub(r",?\s*GLMakie,?", "", line)
            # Remove trailing/leading commas and extra spaces
            line = re.sub(r"using\s*,", "using ", line)
            line = re.sub(r",\s*;", ";", line)
            # If nothing left after 'using', skip the line
            if re.match(r"^\s*using\s*;?\s*$", line):
                continue
            # If the line is now empty, skip it
            if not line.strip():
                continue
        # Remove lines that define or use fig, ax, or call lines!
        if stripped == "fig":
            continue

        if any(func in stripped for func in remove_functions):
            continue
        new_lines.append(line)
    return "\n".join(new_lines)


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

    code = _remove_plotting(code)

    print(f"Shortened code:\n{code}")

    return code
