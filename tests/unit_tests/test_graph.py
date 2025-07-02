import pytest

from jutulgpt.graph import graph


def test_invoke_graph():
    question = "What is the capital of France?"
    result = graph.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )
    assert result is not None
