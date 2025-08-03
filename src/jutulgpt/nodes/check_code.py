"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

import jutulgpt.state as state

# from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.utils import (
    replace_case,
    shorten_first_argument,
)


def shorter_simulations(code: str) -> str:
    """
    In the case when some simulation is called, this function replaces it with a shorter simulation.
    """
    simulation_functions = [
        "simulate_reservoir",
    ]
    original_code = code

    code = replace_case(
        code=code, case_name="case", simulation_functions=simulation_functions
    )
    code = replace_case(
        code=code, case_name="dt", simulation_functions=simulation_functions
    )

    if original_code == code:
        # WARNING: If the previous functions have not changed the code, it might inidate that some other name is used. However, this might we a weird assumption?
        code = shorten_first_argument(
            code=code, simulation_functions=simulation_functions
        )

    return code


def fix_fimbul_imports(code_block: state.CodeBlock) -> state.CodeBlock:
    if "Fimbul" not in code_block.imports:
        return code_block  # No need to fix if Fimbul is not imported
    imports = 'using Pkg; Pkg.activate(".");\n' + code_block.imports
    return state.CodeBlock(imports=imports, code=code_block.code)
