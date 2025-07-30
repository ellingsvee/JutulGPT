"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

from typing import cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from rich.console import Console

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.cli.cli_utils import cli_response_on_check_code
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.human_in_the_loop import response_on_check_code
from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.utils import (
    get_last_code_response,
    load_chat_model,
    remove_plotting,
    replace_case,
    shorten_first_argument,
)


def check_code(state: State, config: RunnableConfig, console: Console):
    configuration = BaseConfiguration.from_runnable_config(config)

    # Get the code block to check
    code_block = get_last_code_response(state)

    # Human interaction to potentially modify the code of not check it
    check_code_bool = True
    extra_messages = []

    if configuration.human_interaction:
        if configuration.cli_mode:
            # CLI mode: use interactive CLI code review
            code_block, check_code_bool, extra_messages = cli_response_on_check_code(
                console, code_block
            )
        else:
            # UI mode: use the original UI-based interaction
            code_block, check_code_bool, extra_messages = response_on_check_code(
                code_block,
            )

    # Return early if the user chose to ignore the code check
    if not check_code_bool:
        return {"error": False}

    imports = code_block.imports
    code = code_block.code

    # WARNING: If we try to use the Fimbul package, we for some reason need to activate the package environment. This should be fixed in the future.
    imports = fix_fimbul_imports(imports)

    # Test the full code
    full_code = imports + "\n" + code

    print_to_console(
        console=console,
        text="Running code...",
        title="Code Runner",
        border_style=colorscheme.warning,
    )

    result = run_string(full_code)

    if result["error"]:
        julia_error_message = get_error_message(result)

        print_to_console(
            console=console,
            text="Code failed!",
            title="Code Runner",
            border_style=colorscheme.error,
        )

        error_message = gen_error_message_string(
            full_code=full_code,
            julia_error_message=julia_error_message,
            config=config,
            console=console,
        )
        # print(f"check_code: {error_message.content}")

        return {
            "messages": extra_messages
            + [SystemMessage(content="Error occurred while running Julia code.")]
            + [error_message],
            "error": True,
            "error_message": error_message.content,
            "iterations": state.iterations + 1,
        }

    print_to_console(
        console=console,
        text="Code succeded!",
        title="Code Runner",
        border_style=colorscheme.success,
    )

    # If everything succeeded, return success
    return {
        "messages": extra_messages
        + [SystemMessage(content="Code executed successfully.")],
        "error": False,
        "iterations": 0,
    }


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

    code = remove_plotting(code)

    return code


def fix_fimbul_imports(imports: str) -> str:
    if "Fimbul" not in imports:
        return imports  # No need to fix if Fimbul is not imported
    imports = 'using Pkg; Pkg.activate(".");\n' + imports
    return imports


def gen_error_message_string(
    full_code: str, julia_error_message: str, config: RunnableConfig, console: Console
) -> AIMessage:
    configuration = BaseConfiguration.from_runnable_config(config)
    # Initialize the model with tool binding. Change the model or add more tools here.
    model = load_chat_model(configuration.response_model).bind_tools(tools)
    system_message = configuration.error_analyzer_prompt

    message = f"""
    Failure in code execution. The code failed with the following Julia error message:
    {julia_error_message}
    The code that failed is:
    ```julia
    {full_code}
    ```
    """

    # Get the model's response
    response = cast(
        AIMessage,
        model.invoke(
            [
                SystemMessage(content=system_message),
                HumanMessage(content=message),
            ],
            config,
        ),
    )

    if response.content.strip():
        print_to_console(
            console,
            response.content,
            title="Error analyzer",
            border_style=colorscheme.tool,
        )

    return response
