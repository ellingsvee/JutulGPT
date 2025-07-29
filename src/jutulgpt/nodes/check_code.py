"""This module contains the `check_code` function which is responsible for evaluating code if it is run."""

from typing import cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from jutulgpt.configuration import BaseConfiguration
from jutulgpt.human_in_the_loop import response_on_check_code
from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.nodes._tools import tools
from jutulgpt.state import State
from jutulgpt.utils import (
    check_for_package_install,
    get_last_code_response,
    load_chat_model,
    remove_plotting,
    replace_case,
    shorten_first_argument,
)


def check_code(state: State, config: RunnableConfig):
    configuration = BaseConfiguration.from_runnable_config(config)

    # Get the code block to check
    code_block = get_last_code_response(state)

    # Human interaction to potentially modify the code of not check it
    code_block, check_code_bool, extra_messages = response_on_check_code(
        code_block, human_interaction=configuration.human_interaction
    )

    # Return early if the user chose to ignore the code check
    if not check_code_bool:
        return {"error": False}

    imports = code_block.imports
    code = code_block.code

    # Disallow package installation if not permitted
    if not configuration.allow_package_installation and check_for_package_install(
        code_block
    ):
        error_message = (
            "The code you generated tries to install a package, which is not allowed. "
            "If you are certain that the package is needed, ask the user to manually install it."
        )
        return {
            "messages": extra_messages + [HumanMessage(content=error_message)],
            "error": True,
            "error_message": error_message,
            "iterations": state.iterations + 1,
        }

    # Preprocess code to shorten simulations and remove plotting (naive implementation)
    # imports = shorter_simulations(imports)
    # code = shorter_simulations(code)

    # WARNING: If we try to use the Fimbul package, we for some reason need to activate the package environment. This should be fixed in the future.
    imports = fix_fimbul_imports(imports)

    # Test the full code
    full_code = imports + "\n" + code
    print("BEFORE run_string")
    result = run_string(full_code)
    print("AFTER run_string")
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = gen_error_message_string(
            full_code=full_code, julia_error_message=julia_error_message, config=config
        )
        print(f"check_code: {error_message.content}")
        return {
            "messages": extra_messages
            + [SystemMessage(content="Error occurred while running Julia code.")]
            + [error_message],
            "error": True,
            "error_message": error_message.content,
            "iterations": state.iterations + 1,
        }

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
    full_code: str, julia_error_message: str, config: RunnableConfig
) -> AIMessage:
    print("INVOKING AI TO FIX ERROR!")

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
    return response
