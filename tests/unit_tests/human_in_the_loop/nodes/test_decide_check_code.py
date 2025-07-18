from unittest.mock import MagicMock, patch

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END

from jutulgpt.human_in_the_loop.nodes.decide_check_code import decide_check_code
from jutulgpt.state import State


@pytest.fixture
def dummy_state():
    class DummyCodeBlock:
        imports = "import foo"
        code = "bar()"

    state = MagicMock(spec=State)
    state.messages = []
    # Patch get_last_code_response to return this
    return state, DummyCodeBlock()


@pytest.fixture
def empty_code_state():
    class DummyCodeBlock:
        imports = ""
        code = ""

    state = MagicMock(spec=State)
    state.messages = []
    return state, DummyCodeBlock()


@patch(
    "jutulgpt.human_in_the_loop.nodes.decide_check_code.interactive_environment", True
)
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.Configuration")
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.get_last_code_response")
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.interrupt")
def test_decide_check_code_accept(
    mock_interrupt, mock_get_last, mock_config, dummy_state
):
    state, code_block = dummy_state
    mock_get_last.return_value = code_block
    mock_config.from_runnable_config.return_value.check_code_bool = True
    mock_interrupt.return_value = [{"type": "accept"}]
    result = decide_check_code(state, RunnableConfig())
    assert result.goto == "check_code"


@patch(
    "jutulgpt.human_in_the_loop.nodes.decide_check_code.interactive_environment", True
)
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.Configuration")
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.get_last_code_response")
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.interrupt")
def test_decide_check_code_ignore(
    mock_interrupt, mock_get_last, mock_config, dummy_state
):
    state, code_block = dummy_state
    mock_get_last.return_value = code_block
    mock_config.from_runnable_config.return_value.check_code_bool = True
    mock_interrupt.return_value = [{"type": "ignore"}]
    result = decide_check_code(state, RunnableConfig())
    assert result.goto.node == END


@patch(
    "jutulgpt.human_in_the_loop.nodes.decide_check_code.interactive_environment", True
)
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.Configuration")
@patch("jutulgpt.human_in_the_loop.nodes.decide_check_code.get_last_code_response")
def test_decide_check_code_no_code(mock_get_last, mock_config, empty_code_state):
    state, code_block = empty_code_state
    mock_get_last.return_value = code_block
    mock_config.from_runnable_config.return_value.check_code_bool = True
    result = decide_check_code(state, RunnableConfig())
    assert result.goto.node == END


@patch(
    "jutulgpt.human_in_the_loop.nodes.decide_check_code.interactive_environment", False
)
def test_decide_check_code_non_interactive(dummy_state):
    state, _ = dummy_state
    result = decide_check_code(state, RunnableConfig())
    assert result.goto == "check_code"
