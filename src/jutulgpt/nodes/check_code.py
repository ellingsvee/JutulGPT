from jutulgpt.julia_interface import run_string
from jutulgpt.state import GraphState


def code_check(state: GraphState):
    """
    Check code

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, error
    """

    print("---CHECKING CODE---")

    # State
    messages = state["messages"]
    code_solution = state["generation"]
    iterations = state["iterations"]

    # Get solution components
    imports = code_solution.imports
    code = code_solution.code

    # Check imports
    result = run_string(imports)
    if result["error"]:
        print("---CODE IMPORT CHECK: FAILED---")
        error_message = [("user", f"Import test failed:\n{result['error_message']}")]
        messages += error_message
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }

    # Check code execution
    result = run_string(imports + "\n" + code)
    if result["error"]:
        print("---CODE BLOCK CHECK: FAILED---")
        error_message = [("user", f"Code execution failed:\n{result['error_message']}")]
        messages += error_message
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "yes",
        }

    # No errors
    print("---NO CODE TEST FAILURES---")
    return {
        "generation": code_solution,
        "messages": messages,
        "iterations": iterations,
        "error": "no",
    }
