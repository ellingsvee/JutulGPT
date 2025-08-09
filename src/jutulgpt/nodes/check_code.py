from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.human_in_the_loop.cli import response_on_check_code, response_on_error
from jutulgpt.julia import get_error_message, get_linting_result, run_code
from jutulgpt.state import State
from jutulgpt.utils import (
    add_julia_context,
    fix_imports,
    get_code_from_response,
    shorter_simulations,
)


def _run_linter(code: str) -> tuple[str, bool]:
    """
    Returns:
        str: String containing the linting issues found in the code. Empty if no issues found.
        bool: True if issues were found, False otherwise.
    """
    linting_result = get_linting_result(code)
    if linting_result:
        linting_message = (
            "## Linter issues found:\n"
            + "Linter returned the following issues:\n"
            + linting_result
        )
        return linting_message, True
    return "", False


def _run_julia_code(code: str, print_code: bool = False) -> tuple[str, bool]:
    """
    Returns:
        str: String containing the code running failed. Empty if the code executed successfully.
        bool: True if issues were found, False otherwise.
    """

    if print_code:
        code_within_julia_context = f"```julia\n{code}```"
        print_to_console(
            text="Running code:\n" + code_within_julia_context[:500] + "...",
            title="Code Runner",
            border_style=colorscheme.warning,
        )
    print_to_console(
        text="Running code...",
        title="Code Runner",
        border_style=colorscheme.warning,
    )

    # result = run_string(code)
    result = run_code(code)

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
    code = code_block.get_full_code()

    # Return early if no code is present
    if code_block.is_empty():
        return {"error": False}

    messages_list = []
    check_code_bool = True
    user_response = ""
    new_code = code
    if configuration.human_interaction.code_check and cli_mode:
        check_code_bool, user_response, new_code = response_on_check_code(code=code)

    # Return early if user provides response or does not want to check code
    if user_response:
        return {"error": True, "messages": [HumanMessage(content=user_response)]}
    if not check_code_bool:
        return {"error": False}

    code_updated = False
    if new_code != code:
        code_updated = True
        code = new_code
        code_update_message = (
            "The code was manually updated to the following. "
            + "This is what will be checked:\n"
            + add_julia_context(code)
        )
        messages_list.append(HumanMessage(content=code_update_message))

    # Hangle the importing of the Fimbul and GLMakie package
    code = fix_imports(code)

    # Then shorten the code for faster simulations
    code = shorter_simulations(code)

    # Running the linter
    linting_message, linting_issues_found = _run_linter(code)

    # Running the code
    code_running_message, code_running_issues_found = _run_julia_code(code)

    # If we did not find any issues, we return the final code
    if not linting_issues_found and not code_running_issues_found:
        return {"error": False, "messages": messages_list}

    # If we found issues, we prepare the feedback messages
    feedback_message = "# Code check issues found. Please use these to fix your code:\n"
    if linting_issues_found:
        feedback_message += linting_message + "\n"
    if code_running_issues_found:
        feedback_message += code_running_message

    # Return the feedback messages and and error flag
    messages_list.append(HumanMessage(content=feedback_message))

    # If the code fails, the human can skip the fixing.
    check_code_bool = True
    user_response = ""
    if configuration.human_interaction.fix_error and cli_mode:
        check_code_bool, user_response = response_on_error()

    if not check_code_bool:
        messages_list.append(
            HumanMessage(
                content="The code failed, but the user decided to skip fixing it."
            )
        )
        return {"messages": messages_list, "error": False}
    if user_response:
        messages_list.append(HumanMessage(content=user_response))

    if code_updated:
        new_code_block = get_code_from_response(code, within_julia_context=False)
        return {"messages": messages_list, "error": True, "code_block": new_code_block}
    return {"messages": messages_list, "error": True}
