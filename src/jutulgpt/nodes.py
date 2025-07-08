from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import MessagesState

from jutulgpt.agents import (
    agent_config,
    code_gen_chain,
    # code_gen_chain_without_tools,
    get_structured_response,
)
from jutulgpt.config import llm
from jutulgpt.julia_interface import get_error_message, run_string

# from jutulgpt.prompts import gen_system_message
from jutulgpt.rag import (
    docs_retriever,
    examples_retriever,
    format_docs,
    format_examples,
)
from jutulgpt.state import Code, GraphState
from jutulgpt.utils import format_code_response, logger


def generate_code(state: GraphState) -> GraphState:
    response = code_gen_chain.invoke(
        {
            "messages": state.messages,
        },
        config=agent_config,
    )

    structured_response = get_structured_response(response)
    return GraphState(
        messages=response["messages"],
        structured_response=structured_response,
        error=False,
        iterations=state.iterations + 1,
    )


def check_code(state: GraphState) -> GraphState:
    messages = state.messages
    structured_resonse = state.structured_response
    prefix = structured_resonse.prefix
    imports = structured_resonse.imports
    code = structured_resonse.code

    if prefix == "" and imports == "" and code == "":
        error_message = f"Your response is empty. You have to provide an answer!"
        messages.append(HumanMessage(content=error_message))
        return GraphState(
            messages=messages,
            structured_response=structured_resonse,
            error=True,
            iterations=state.iterations,
        )

    result = run_string(imports)
    if result["error"]:
        julia_error_message = get_error_message(result)
        error_message = f"Your solution failed the import test:\n{julia_error_message}"

        # logger.info(
        #     f"""
        #     Import test failed.
        #     Imports that failed: {imports}
        #     {julia_error_message}
        #     """
        # )
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

    # logger.info("No code test failures.")
    return GraphState(
        messages=messages,
        structured_response=structured_resonse,
        error=False,
        iterations=state.iterations,
    )
