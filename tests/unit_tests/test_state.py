import pytest

from jutulgpt.state import Code, GraphState, make_initial_state


def test_code_model_fields():
    code = Code(prefix="desc", imports="import os", code="print('hi')")
    assert code.prefix == "desc"
    assert code.imports == "import os"
    assert code.code == "print('hi')"
    # Test default values
    code2 = Code()
    assert code2.prefix == ""
    assert code2.imports == ""
    assert code2.code == ""


def test_graph_state_fields():
    code = Code(prefix="desc", imports="import sys", code="print('test')")
    messages = ["msg1", "msg2"]
    state = GraphState(
        messages=messages,
        structured_response=code,
        error=True,
        iterations=2,
        docs_context="docs",
        examples_context="examples",
    )
    assert state.messages == messages
    assert state.structured_response == code
    assert state.error is True
    assert state.iterations == 2
    assert state.docs_context == "docs"
    assert state.examples_context == "examples"


def test_graph_state_is_frozen():
    code = Code(prefix="desc", imports="import sys", code="print('test')")
    state = GraphState(
        messages=[],
        structured_response=code,
        error=False,
        iterations=0,
        docs_context="",
        examples_context="",
    )
    try:
        state.iterations = 5
        assert False, "Should not be able to modify frozen dataclass"
    except Exception as e:
        assert isinstance(e, (AttributeError, TypeError))


def test_make_initial_state():
    question = "What is the CartesianMesh function?"
    state = make_initial_state(question)
    assert isinstance(state, GraphState)
    assert len(state.messages) == 1
    assert state.messages[0].content == question
    assert state.structured_response == Code(prefix="", imports="", code="")
    assert state.error is False
    assert state.iterations == 0
    assert state.docs_context == ""
    assert state.examples_context == ""
