from langchain_core.messages import AIMessage
from langgraph.graph import MessagesState

from jutulgpt.agents import (
    code_gen_chain,
    concatenated_content,
    code_gen_or_retrieval_chain,
)
from jutulgpt.state import GraphState
from jutulgpt.utils import format_code_response, logger
from jutulgpt.config import llm
from jutulgpt.state import Code
from jutulgpt.tools.tools_rag import docs_retriever_tool


def generate(state: GraphState) -> GraphState:
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
                "Now, try again. Structure the output with a prefix, imports, and code block:",
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
    # messages.append(
    #     (
    #         "assistant",
    #         format_code_response(code_solution),
    #     )
    # )

    # Increment
    # iterations = iterations + 1
    # return {
    #     "messages": messages,
    #     "code": code_solution,
    #     "error": "no",
    #     "iterations": iterations,
    # }

    state["messages"].append(AIMessage(content=format_code_response(code_solution)))
    state["code"] = code_solution
    state["error"] = "no"
    state["iterations"] += 1
    return state


# def generate_code_or_retrieve(state: GraphState) -> GraphState:
#     messages = state["messages"]
#     code_result = code_gen_or_retrieval_chain.invoke({"messages": messages})
#
#
def generate_code(state: GraphState) -> GraphState:
    messages = state["messages"]
    iterations = state["iterations"]
    error = state["error"]
    context = state["context"]

    code_solution = code_gen_chain.invoke({"context": context, "messages": messages})

    return state
