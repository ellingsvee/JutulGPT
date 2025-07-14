from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph import END

from jutulgpt.graph import decide_to_finish, graph
from jutulgpt.state import State


def make_state(error=False, iterations=0, is_last_step=False):
    return State(
        messages=[],
        error=error,
        error_message="",
        is_last_step=is_last_step,
        iterations=iterations,
    )


def test_decide_to_finish_end_on_no_error():
    state = make_state(error=False, iterations=0)
    assert decide_to_finish(state) == END


def test_decide_to_finish_end_on_max_iterations():
    from jutulgpt.configuration import static_config

    state = make_state(error=True, iterations=static_config.max_iterations)
    assert decide_to_finish(state) == END


def test_decide_to_finish_continue():
    state = make_state(error=True, iterations=0)
    assert decide_to_finish(state) == "generate_response"


@patch("jutulgpt.graph.generate_response")
@patch("jutulgpt.graph.tools_node")
@patch("jutulgpt.graph.check_code")
def test_graph_runs_minimal_flow(
    mock_check_code, mock_tools_node, mock_generate_response
):
    # Mock node outputs
    mock_generate_response.return_value = {
        "messages": [],
        "iterations": 0,
        "error": False,
    }
    mock_tools_node.return_value = {"messages": [], "iterations": 0, "error": False}
    mock_check_code.return_value = {"messages": [], "iterations": 1, "error": False}

    # Minimal state to start
    state = make_state()
    # Run the graph for a few steps
    outputs = []
    for step in graph.stream(state):
        outputs.append(step)
        # Stop after a few steps to avoid infinite loop in test
        if len(outputs) > 3:
            break
    assert outputs  # Should have at least one output
