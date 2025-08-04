from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from jutulgpt.julia import (
    get_function_documentation,
)
from jutulgpt.state import State
from jutulgpt.utils import (
    _get_code_string_from_response,
)


def get_relevant_function_documentation(
    state: State,
    config: RunnableConfig,
):
    if not state.code_block.is_empty():
        return _get_relevant_function_documentation_from_code(state, config)

    if state.retrieved_context:
        return _get_relevant_function_documentation_from_retrieved_context(
            state, config
        )

    return {}


def _get_relevant_function_documentation_from_retrieved_context(
    state: State,
    config: RunnableConfig,
):
    retrieved_context = state.retrieved_context

    # Get the code from the retrieved context
    full_code = _get_code_string_from_response(retrieved_context)

    _, retrieved_function_documentation = get_function_documentation(full_code)

    # If any documentation was retrieved, add it ot the state
    if retrieved_function_documentation:
        return {"retrieved_function_documentation": retrieved_function_documentation}
    return {}


def _get_relevant_function_documentation_from_code(
    state: State,
    config: RunnableConfig,
):
    code_block = state.code_block

    # Try to retrieve the function documentation from the code
    _, retrieved_function_documentation = get_function_documentation(
        code_block.get_full_code()
    )

    # If any documentation was retrieved, add it ot the state
    if retrieved_function_documentation:
        return {"retrieved_function_documentation": retrieved_function_documentation}
    return {}
