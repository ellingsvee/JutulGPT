from os import stat

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import MessagesState

from jutulgpt.agents import code_gen_chain, get_structured_response
from jutulgpt.config import llm
from jutulgpt.julia_interface import get_error_message, run_string
from jutulgpt.rag import (
    docs_retriever,
    examples_retriever,
    format_docs,
    format_examples,
)
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
    # out = code_gen_chain.invoke({"messages": messages})
    out = code_gen_chain.invoke(
        {
            "messages": messages,
            "docs_context": state.docs_context,
            "examples_context": state.examples_context,
        }
    )
    structured_resonse = get_structured_response(out)

    # TODO: Double check that this is correct.
    messages.append(AIMessage(content=format_code_response(structured_resonse)))
    return GraphState(
        messages=messages,
        structured_response=structured_resonse,
        error=False,
        iterations=state.iterations + 1,
        docs_context=state.docs_context,
        examples_context=state.examples_context,
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
            docs_context=state.docs_context,
            examples_context=state.examples_context,
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
            docs_context=state.docs_context,
            examples_context=state.examples_context,
        )

    logger.info("No code test failures.")
    return GraphState(
        messages=messages,
        structured_response=structured_resonse,
        error=False,
        iterations=state.iterations,
        docs_context=state.docs_context,
        examples_context=state.examples_context,
    )


def retrieve_info(state: GraphState) -> GraphState:
    # Get the latest user message as the query
    user_messages = [m for m in state.messages if getattr(m, "type", None) == "human"]
    if user_messages:
        query = user_messages[-1].content
    else:
        query = ""
    docs_context = format_docs(docs_retriever.invoke(input=query))
    examples_context = format_examples(examples_retriever.invoke(input=query))
    return GraphState(
        messages=state.messages,
        structured_response=state.structured_response,
        error=False,
        iterations=state.iterations,
        docs_context=docs_context,
        examples_context=examples_context,
    )
