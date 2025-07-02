from jutulgpt.julia_interface import run_string
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
        # print("---CODE IMPORT CHECK: FAILED---")
        logger.error("Code import check failed.")
        logger.debug(f"Imports that failed:\n{imports}")
        error_message = [("user", f"Import test failed:\n{result['error_message']}")]
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
        # print("---CODE BLOCK CHECK: FAILED---")
        # print(f"Code that failed:\n{full_code}")
        error_message = [("user", f"Code execution failed:\n{result['error_message']}")]
        # print(f"Error message:\n{error_message}")
        logger.error("Code block check failed.")
        logger.debug(f"Code that failed:\n{full_code}")
        logger.debug(f"Error message:\n{result['error_message']}")

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
