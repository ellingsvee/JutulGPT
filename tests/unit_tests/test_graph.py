from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from jutulgpt.config import max_iterations
from jutulgpt.graph import (
    check_code_name,
    decide_to_finish,
    end_name,
    generate_code_name,
    graph,
    start_name,
)
from jutulgpt.nodes import check_code, generate_code
from jutulgpt.state import Code, GraphState


def test_graph_nodes():
    # Check that the compiled graph has the expected nodes
    nodes = set(graph.get_graph().nodes)
    assert generate_code_name in nodes
    assert check_code_name in nodes


def test_decide_to_finish_end():
    # Should finish if no error or max_iterations reached
    state = GraphState(
        messages=[],
        structured_response=Code(prefix="", imports="", code=""),
        error=False,
        iterations=0,
    )
    assert decide_to_finish(state) == end_name

    state = GraphState(
        messages=[],
        structured_response=Code(prefix="", imports="", code=""),
        error=True,
        iterations=max_iterations,
    )
    # Assuming max_iterations=10 in config
    assert decide_to_finish(state) == end_name


def test_decide_to_finish_retry():
    # Should retry if error and not max_iterations
    state = GraphState(
        messages=[],
        structured_response=Code(prefix="", imports="", code=""),
        error=True,
        iterations=1,
    )
    assert decide_to_finish(state) == generate_code_name
