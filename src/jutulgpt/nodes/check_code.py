from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.state import GraphState
from jutulgpt.utils import logger


def code_check(state: GraphState) -> GraphState:
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
    code_solution = state["code"]

    # Get solution components
    imports = code_solution.imports
    code = code_solution.code

    # Check imports
    result = run_string(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        # error_message = [("user", f"Import test failed:\n{julia_error_message}")]
        error_message = [
            SystemMessage(content=f"Import test failed:\n{julia_error_message}")
        ]

        logger.info(
            f"""
            Import test failed.
            Imports that failed: {imports}
            {julia_error_message}
            """
        )
        state["messages"] += error_message
        state["error"] = "yes"
        return state

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
        state["messages"] += error_message
        state["error"] = "yes"
        return state

    logger.info("No code test failures.")
    state["messages"].append(
        SystemMessage(content="No code test failures. Code is valid.")
    )
    state["error"] = "no"
    return state
