from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

import jutulgpt.state as state
from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.cli.cli_human_interaction import (
    cli_response_on_check_code,
    cli_response_on_error,
)
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.human_in_the_loop import response_on_error
from jutulgpt.julia import (
    get_error_message,
    get_linting_result,
    run_code,
)
from jutulgpt.state import State

# from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.utils import (
    replace_case,
    shorten_first_argument,
)


def _shorter_simulations(code: str) -> str:
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


def _fix_fimbul_imports(code_block: state.CodeBlock) -> state.CodeBlock:
    if "Fimbul" not in code_block.imports:
        return code_block  # No need to fix if Fimbul is not imported
    imports = 'using Pkg; Pkg.activate(".");\n' + code_block.imports
    return state.CodeBlock(imports=imports, code=code_block.code)


def _run_linter(full_code: str) -> tuple[str, bool]:
    """
    Returns:
        str: String containing the linting issues found in the code. Empty if no issues found.
        bool: True if issues were found, False otherwise.
    """
    linting_result = get_linting_result(full_code)
    if linting_result:
        linting_message = (
            "## Linter issues found:\n"
            + "Linter returned the following issues:\n"
            + linting_result
        )
        return linting_message, True
    return "", False


def _run_julia_code(full_code: str) -> tuple[str, bool]:
    """
    Returns:
        str: String containing the code running failed. Empty if the code executed successfully.
        bool: True if issues were found, False otherwise.
    """

    print_to_console(
        text="Running code...",
        title="Code Runner",
        border_style=colorscheme.warning,
    )

    # result = run_string(full_code)
    result = run_code(full_code)

    if result.get("error", False):
        julia_error_message = get_error_message(result)

        print_to_console(
            text=f"Code failed!\n\n{julia_error_message}",
            title="Code Runner",
            border_style=colorscheme.error,
        )

        code_runner_error_message = (
            "## Code runner error:\n"
            + "Running the code generated failed with the following error:\n"
            + julia_error_message
        )
        return code_runner_error_message, True

    print_to_console(
        text=f"Code succeded in {round(result['runtime'], 2)} seconds!",
        title="Code Runner",
        border_style=colorscheme.success,
    )

    return "", False


def check_code(
    state: State,
    config: RunnableConfig,
):
    configuration = BaseConfiguration.from_runnable_config(config)
    code_block = state.code_block

    if code_block.is_empty():
        return {"error": False}

    check_code_bool = True
    if configuration.human_interaction.code_check:
        check_code_bool = cli_response_on_check_code()

    # Return early if the user chose to ignore the code check
    if not check_code_bool:
        return {"error": False}

    # First fix the use of the Fimbul package
    code_block = _fix_fimbul_imports(code_block)

    # Then shorten the code for faster simulations
    full_code = _shorter_simulations(code_block.get_full_code())

    # Running the linter
    linting_message, linting_issues_found = _run_linter(full_code)

    # Running the code
    code_running_message, code_running_issues_found = _run_julia_code(full_code)

    # If we did not find any issues, we return the final code
    if not linting_issues_found and not code_running_issues_found:
        return {"error": False}

    # If we found issues, we prepare the feedback messages
    feedback_message = "# Code check issues found. Please use these to fix your code:\n"
    if linting_issues_found:
        feedback_message += linting_message + "\n"
    if code_running_issues_found:
        feedback_message += code_running_message

    feedback_list = [HumanMessage(content=feedback_message)]

    # If the code fails, the user has the option of trying to fix the code or not.
    # The user also gets the option to give some additional feedback that might help the agent
    try_to_fix_code_bool, additional_feedback = True, ""
    if configuration.human_interaction.decide_to_try_to_fix_error:
        if cli_mode:
            try_to_fix_code_bool, additional_feedback = cli_response_on_error()
        else:  # UI mode
            try_to_fix_code_bool, additional_feedback = response_on_error()

    # If the user does not want to try to fix the code
    if not try_to_fix_code_bool:
        feedback_list.append(
            HumanMessage(
                content="The code failed, but the user chose to not try to fix the error."
            )
        )
        return {"messages": feedback_list, "error": False}

    # If the user provided additional feedback
    if additional_feedback:
        feedback_list.append(HumanMessage(content=additional_feedback))

    # Return the feedback messages and and error flag
    return {"messages": feedback_list, "error": True}
