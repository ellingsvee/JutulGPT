from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from jutulgpt.nodes import check_code, generate_code, retrieve_info
from jutulgpt.state import Code, GraphState


@pytest.fixture
def dummy_state():
    return GraphState(
        messages=[HumanMessage(content="How do I solve X in Julia?")],
        structured_response=Code(prefix="", imports="", code=""),
        error=False,
        iterations=0,
        docs_context="",
        examples_context="",
    )


@patch("jutulgpt.nodes.code_gen_chain")
@patch("jutulgpt.nodes.get_structured_response")
@patch("jutulgpt.nodes.format_code_response")
def test_generate_code(mock_format, mock_structured, mock_chain, dummy_state):
    # Setup mock
    mock_structured.return_value = Code(
        prefix="", imports="import A", code='println("Hello")'
    )
    mock_format.return_value = "Formatted code block"
    mock_chain.invoke.return_value = MagicMock()

    result = generate_code(dummy_state)

    assert isinstance(result, GraphState)
    assert isinstance(result.messages[-1], AIMessage)
    assert result.error is False
    assert result.iterations == 1


@patch("jutulgpt.nodes.run_string")
@patch("jutulgpt.nodes.get_error_message")
def test_check_code_success(mock_get_error_message, mock_run_string, dummy_state):
    # Setup mock for successful import and execution
    mock_run_string.return_value = {
        "out": "",
        "error": False,
        "error_message": "",
        "error_stacktrace": "",
    }

    result = check_code(dummy_state)

    assert isinstance(result, GraphState)
    assert result.error is False
    assert result.iterations == 0


@patch("jutulgpt.nodes.run_string")
@patch("jutulgpt.nodes.get_error_message")
def test_check_code_fail(mock_get_error_message, mock_run_string, dummy_state):
    # Setup mock for successful import and execution
    mock_run_string.return_value = {
        "out": "",
        "error": True,
        "error_message": "",
        "error_stacktrace": "",
    }

    result = check_code(dummy_state)

    assert isinstance(result, GraphState)
    assert result.error is True
    assert result.iterations == 0


@patch("jutulgpt.nodes.docs_retriever")
@patch("jutulgpt.nodes.examples_retriever")
@patch("jutulgpt.nodes.format_docs")
@patch("jutulgpt.nodes.format_examples")
def test_retrieve_info(
    mock_fmt_examples, mock_fmt_docs, mock_ex_retriever, mock_doc_retriever, dummy_state
):
    mock_doc_retriever.invoke.return_value = "docs"
    mock_ex_retriever.invoke.return_value = "examples"
    mock_fmt_docs.return_value = "Formatted docs"
    mock_fmt_examples.return_value = "Formatted examples"

    result = retrieve_info(dummy_state)
    assert isinstance(result, GraphState)
    assert result.docs_context == "Formatted docs"
    assert result.examples_context == "Formatted examples"
