from jutulgpt.julia_interface import run_string, get_error_message
from jutulgpt.state import CodeState
from jutulgpt.utils import logger


def code_check(state: CodeState) -> CodeState:
    """
    Check code

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, error
    """

    # print("---CHECKING CODE---")
    logger.info("Checking coder:")

    # State
    messages = state["messages"]
    code_solution = state["code"]
    iterations = state["iterations"]

    # Get solution components
    imports = code_solution.imports
    code = code_solution.code

    # Check imports
    result = run_string(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = [("user", f"Import test failed:\n{julia_error_message}")]

        logger.info(
            f"""
            Import test failed.
            Imports that failed: {imports}
            {julia_error_message}
            """
        )

        messages += error_message
        return {
            "code": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }

    # Check code execution
    full_code = imports + "\n" + code
    result = run_string(full_code)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = [("user", f"Code execution failed:\n{julia_error_message}")]
        logger.info(
            f"""
            Code execution failed.
            Code that failed: {full_code}
            {julia_error_message}
            """
        )
        messages += error_message
        return {
            "code": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }

    # No errors
    # print("---NO CODE TEST FAILURES---")
    logger.info("No code test failures.")
    return {
        "code": code_solution,
        "messages": messages,
        "iterations": iterations,
        "error": "no",
    }
