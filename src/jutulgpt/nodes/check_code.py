"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

import re
from typing import List

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from jutulgpt.configuration import ALLOW_PACKAGE_INSTALLATION
from jutulgpt.human_in_the_loop import check_shortened_code
from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.state import CodeBlock, State
from jutulgpt.utils import get_last_code_response, split_code_into_lines


def check_code(state: State, config: RunnableConfig):
    # Get the code block to check
    code_block = get_last_code_response(state)
    imports = code_block.imports
    code = code_block.code

    # If there is no code, nothing to check
    if not imports and not code:
        return {}

    # Disallow package installation if not permitted
    if not ALLOW_PACKAGE_INSTALLATION and check_for_package_install(code_block):
        error_message = (
            "The code you generated tries to install a package, which is not allowed. "
            "If you are certain that the package is needed, ask the user to manually install it."
        )
        return {
            "messages": [HumanMessage(content=error_message)],
            "error": True,
            "error_message": error_message,
            "iterations": state.iterations + 1,
        }

    # Preprocess code to shorten simulations and remove plotting (naive implementation)
    imports = shorter_simulations(imports)
    code = shorter_simulations(code)

    # Add a human interagtion to check the shortened code
    imports, code = check_shortened_code(imports, code)

    # WARNING: If we try to use the Fimbul package, we for some reason need to activate the package environment. This should be fixed in the future.
    imports = fix_fimbul_imports(imports)

    def gen_error_message_string(test_type: str, julia_error_message: str) -> str:
        # Helper for formatting error messages
        return (
            f"The code from your previous response failed with the following error. Fix it to provide runnable code!\n\n"
            f"Failure in {test_type}. The code failed with the following Julia error message:\n{julia_error_message}"
        )

    # First, test imports only (to catch missing packages or bad imports early)
    result = run_string(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = gen_error_message_string("import test", julia_error_message)
        print(f"check_code: {error_message}")
        return {
            "messages": [HumanMessage(content=error_message)],
            "error": True,
            "error_message": error_message,
            "iterations": state.iterations + 1,
        }

    # Then, test full code (imports + code)
    full_code = imports + "\n" + code
    result = run_string(full_code)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = gen_error_message_string(
            "code execution test", julia_error_message
        )
        print(f"check_code: {error_message}")
        return {
            "messages": [HumanMessage(content=error_message)],
            "error": True,
            "error_message": error_message,
            "iterations": state.iterations + 1,
        }

    # If everything succeeded, return success
    return {
        "messages": [AIMessage(content="Code executed successfully.")],
        "error": False,
        "iterations": 0,
    }


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
        "println",  # To avoid printing to terminal
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

    return code


def check_for_package_install(code_block: CodeBlock) -> bool:
    not_allowed = [
        "using Pkg",  # Pkg is used to install packages, which is not allowed
        "Pkg.add",  # Pkg.add is used to install packages, which is not allowed
        "Pkg.update",  # Pkg.update is used to update packages, which is not allowed
        "Pkg.instantiate",  # Pkg.instantiate is used to install dependencies, which is not allowed
    ]
    if any(item in code_block.imports for item in not_allowed):
        return True
    if any(item in code_block.code for item in not_allowed):
        return True
    return False


def fix_fimbul_imports(imports: str) -> str:
    if "Fimbul" not in imports:
        return imports  # No need to fix if Fimbul is not imported
    imports = 'using Pkg; Pkg.activate(".");\n' + imports
    return imports
