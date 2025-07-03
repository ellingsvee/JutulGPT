from jutulgpt.agents import code_gen_chain, concatenated_content
from jutulgpt.state import CodeState
from jutulgpt.utils import format_code_response, logger


def generate(state: CodeState) -> CodeState:
    """
    Generate a code solution

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation
    """
    # print("---GENERATING CODE SOLUTION---")
    logger.info("Generating code solution.")

    # State
    messages = state["messages"]
    iterations = state["iterations"]
    error = state["error"]

    # We have been routed back to generation with an error
    if error == "yes":
        messages += [
            (
                "user",
                "Now, try again. Invoke the code tool to structure the output with a prefix, imports, and code block:",
            )
        ]

    # Solution
    code_solution = code_gen_chain.invoke(
        {"context": concatenated_content, "messages": messages}
    )
    # messages += [
    #     (
    #         "assistant",
    #         f"{code_solution.prefix} \n Imports: {code_solution.imports} \n Code: {code_solution.code}",
    #     )
    # ]
    messages.append(
        (
            "assistant",
            format_code_response(code_solution),
        )
    )

    # Increment
    iterations = iterations + 1
    return {
        "messages": messages,
        "code": code_solution,
        "error": "no",
        "iterations": iterations,
    }
