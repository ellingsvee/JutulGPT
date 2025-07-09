from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import MessagesState

from jutulgpt.agents import (  # code_gen_chain_without_tools,
    agent_config,
    code_gen_chain,
    get_structured_response,
)
from jutulgpt.config import avoid_tools, llm
from jutulgpt.julia_interface import get_error_message, run_string

# from jutulgpt.prompts import gen_system_message
from jutulgpt.rag import (
    docs_retriever,
    examples_retriever,
    format_docs,
    format_examples,
)
from jutulgpt.state import Code, GraphState, InputState
from jutulgpt.utils import format_code_response, logger, state_to_dict


def start_node(state: InputState) -> GraphState:
    """
    Start node that sets up the conversation with the user.
    """

    retrieve_context_dict = {}
    if avoid_tools:
        retrieve_context_dict = {"retrieved_context": ""}

    return GraphState(
        messages=state.messages,
        structured_response=Code(prefix="", imports="", code=""),
        error=False,
        iterations=0,
        **retrieve_context_dict,
    )


def retrieve_context(state: GraphState) -> GraphState:
    messages = state.messages
    if not messages or not isinstance(messages[-1], HumanMessage):
        raise ValueError("The last message must be a HumanMessage.")
    user_question = messages[-1].content

    docs = format_docs(docs_retriever.invoke(input=user_question))
    examples = format_examples(examples_retriever.invoke(input=user_question))

    out = f"""
# Retrieved from the JutulDarcy documentation:
{docs}

# Retrieved from the JutulDarcy examples:
{examples}
"""
    return GraphState(
        retrieved_context=out,
        **state_to_dict(state, remove_keys=["retrieved_context"]),
    )


def generate_code(state: GraphState) -> GraphState:
    # gen_dict = {
    #     "messages": state.messages,
    #     "retrieved_context": state.retrieved_context,
    # }
    # if avoid_tools:
    #     gen_dict["retrieved_context"] = state.retrieved_context

    response = code_gen_chain.invoke(
        {
            "messages": state.messages,
            "retrieved_context": state.retrieved_context if avoid_tools else "",
        },
        config=agent_config,
    )

    structured_response = get_structured_response(response)
    return GraphState(
        messages=response["messages"],
        structured_response=structured_response,
        error=False,
        iterations=state.iterations + 1,
        **state_to_dict(
            state,
            remove_keys=["messages", "structured_response", "error", "iterations"],
        ),
    )


def check_code(state: GraphState) -> GraphState:
    messages = state.messages
    structured_resonse = state.structured_response
    prefix = structured_resonse.prefix
    imports = structured_resonse.imports
    code = structured_resonse.code

    # if prefix == "" and imports == "" and code == "":
    #     error_message = f"Your response is empty. You have to provide an answer!"
    #     messages.append(HumanMessage(content=error_message))
    #     return GraphState(
    #         messages=messages,
    #         structured_response=structured_resonse,
    #         error=True,
    #         **state_to_dict(
    #             state, remove_keys=["messages", "structured_response", "error"]
    #         ),
    #     )

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
            **state_to_dict(
                state, remove_keys=["messages", "structured_response", "error"]
            ),
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
            **state_to_dict(
                state, remove_keys=["messages", "structured_response", "error"]
            ),
        )

    logger.info("No code test failures.")
    return GraphState(
        messages=messages,
        structured_response=structured_resonse,
        error=False,
        **state_to_dict(
            state, remove_keys=["messages", "structured_response", "error"]
        ),
    )
