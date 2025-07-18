from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from jutulgpt.human_in_the_loop.nodes.response_on_generated_code import (
    response_on_generated_code,
)
from jutulgpt.state import State


@pytest.fixture
def dummy_state():
    class DummyCodeBlock:
        imports = "using Foo"
        code = "bar()"

    state = MagicMock(spec=State)
    state.messages = []
    return state, DummyCodeBlock()


@patch(
    "jutulgpt.human_in_the_loop.nodes.response_on_generated_code.interactive_environment",
    True,
)
@patch("jutulgpt.human_in_the_loop.nodes.response_on_generated_code.Configuration")
@patch(
    "jutulgpt.human_in_the_loop.nodes.response_on_generated_code.get_last_code_response"
)
@patch("jutulgpt.human_in_the_loop.nodes.response_on_generated_code.interrupt")
def test_response_on_generated_code_edit(
    mock_interrupt, mock_get_last, mock_config, dummy_state
):
    state, code_block = dummy_state
    mock_get_last.return_value = code_block
    mock_config.from_runnable_config.return_value = MagicMock()
    # Simulate user editing the code
    mock_interrupt.return_value = [
        {
            "type": "edit",
            "args": {
                "args": {"code": '```julia\nusing Foo\nbar()\nprintln("changed")\n```'}
            },
        }
    ]
    result = response_on_generated_code(state, MagicMock())
    assert "messages" in result
    assert isinstance(result["messages"][0], AIMessage)
    assert "changed" in result["messages"][0].content


@patch(
    "jutulgpt.human_in_the_loop.nodes.response_on_generated_code.interactive_environment",
    True,
)
@patch("jutulgpt.human_in_the_loop.nodes.response_on_generated_code.Configuration")
@patch(
    "jutulgpt.human_in_the_loop.nodes.response_on_generated_code.get_last_code_response"
)
@patch("jutulgpt.human_in_the_loop.nodes.response_on_generated_code.interrupt")
def test_response_on_generated_code_ignore(
    mock_interrupt, mock_get_last, mock_config, dummy_state
):
    state, code_block = dummy_state
    mock_get_last.return_value = code_block
    mock_config.from_runnable_config.return_value = MagicMock()
    # Simulate user ignoring the edit
    mock_interrupt.return_value = [{"type": "ignore"}]
    result = response_on_generated_code(state, MagicMock())
    assert result == {}


@patch(
    "jutulgpt.human_in_the_loop.nodes.response_on_generated_code.interactive_environment",
    False,
)
def test_response_on_generated_code_non_interactive(dummy_state):
    state, _ = dummy_state
    result = response_on_generated_code(state, MagicMock())
    assert result == {}
