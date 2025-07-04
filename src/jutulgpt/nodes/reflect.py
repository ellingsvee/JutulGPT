from langchain_core.messages import AIMessage

from jutulgpt.agents import code_gen_chain, concatenated_content
from jutulgpt.state import GraphState


def reflect(state: GraphState) -> GraphState:
    """
    Reflect on errors

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation
    """

    # State
    messages = state["messages"]
    iterations = state["iterations"]
    code_solution = state["code"]

    # Prompt reflection

    # Add reflection
    reflections = code_gen_chain.invoke(
        {"context": concatenated_content, "messages": messages}
    )
    # messages += [("assistant", f"Here are reflections on the error: {reflections}")]
    # return {"code": code_solution, "messages": messages, "iterations": iterations}
    state["messages"].append(
        AIMessage(content=f"Here are reflections on the error: {reflections}")
    )
    state["code"] = code_solution
    state["error"] = "no"
    return state
