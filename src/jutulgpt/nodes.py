from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState

from jutulgpt.agents import code_gen_chain, get_structured_response
from jutulgpt.config import llm
from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.state import Code, GraphState
from jutulgpt.utils import format_code_response, logger

# from jutulgpt.tools.tools_rag import docs_retriever_tool


def generate_code(state: GraphState) -> GraphState:
    """
    Generate a code solution

    Args:
        state (dict): The current graph state

    Returns:
        state (dict): New key added to state, generation
    """

    # # State
    messages = state.messages
    error = state.error

    # We have been routed back to generation with an error
    if error:
        messages.append(
            HumanMessage(
                content="Now, try again. Structure the output with a prefix, imports, and code block:"
            )
        )

    # Solution
    out = code_gen_chain.invoke({"messages": messages})
    structured_resonse = get_structured_response(out)

    # TODO: Double check that this is correct.
    messages.append(AIMessage(content=format_code_response(structured_resonse)))
    return GraphState(
        messages=messages,
        structured_response=structured_resonse,
        error=False,
        iterations=state.iterations + 1,
    )


def check_code(state: GraphState) -> GraphState:
    messages = state.messages
    structured_resonse = state.structured_response
    imports = structured_resonse.imports
    code = structured_resonse.code

    result = run_string(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = f"Your solution failed the import test:\n{julia_error_message}"

        logger.info(
            f"""
            Import test failed.
            Imports that failed: {imports}
            {julia_error_message}
            """
        )
        messages.append(HumanMessage(content=error_message))
        return GraphState(
            messages=messages,
            structured_response=structured_resonse,
            error=True,
            iterations=state.iterations,
        )

    full_code = imports + "\n" + code
    result = run_string(full_code)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = (
            f"Your solution failed the code execution test:\n{julia_error_message}"
        )
        logger.info(
            f"""
            Code execution failed.
            Code that failed: {full_code}
            {julia_error_message}
            """
        )
        messages.append(HumanMessage(content=error_message))
        return GraphState(
            messages=messages,
            structured_response=structured_resonse,
            error=True,
            iterations=state.iterations,
        )

    logger.info("No code test failures.")
    return GraphState(
        messages=messages,
        structured_response=structured_resonse,
        error=False,
        iterations=state.iterations,
    )
