import pytest

from jutulgpt.julia_interface import (
    _filter_stacktrace,
    _get_code_string_from_response,
    _split_stacktrace,
    get_code_from_response,
    get_error_message,
    run_string,
)
from jutulgpt.state import Code


def test_run_string_valid():
    code = "x = 2; y = x^3; y"
    result = run_string(code)
    assert result["out"] == 8
    assert result["error"] is False
    assert result["error_message"] is None
    assert result["error_stacktrace"] is None


def test_run_string_print_output():
    code = 'println("Hello from Julia!")'
    result = run_string(code)
    assert result["out"] is None  # No return value, just print
    assert result["error"] is False
    assert result["error_message"] is None
    assert result["error_stacktrace"] is None


def test_run_string_error():
    code = "x = 2; y = ; println(y)"
    result = run_string(code)
    assert result["out"] is None
    assert result["error"] is True
    assert result["error_message"] is not None


def test_split_stacktrace_with_stack():
    msg = "Some error\nStacktrace:\n[1] foo()\n[2] bar()"
    pre, stack = _split_stacktrace(msg)
    assert pre == "Some error"
    assert stack == "[1] foo()\n[2] bar()"


def test_split_stacktrace_without_stack():
    msg = "Just an error"
    pre, stack = _split_stacktrace(msg)
    assert pre == "Just an error"
    assert stack is None


def test_get_code_string_from_response_found():
    response = "Here is code:\n```julia\nx = 1\ny = 2\n```"
    code = _get_code_string_from_response(response)
    assert code == "x = 1\ny = 2"


def test_get_code_string_from_response_not_found():
    response = "No code block here."
    code = _get_code_string_from_response(response)
    assert code == ""


def test_get_code_from_response_with_imports():
    response = "```julia\nusing Foo\nusing Bar\nx = 1\ny = 2\n```"
    code_obj = get_code_from_response(response)
    assert code_obj.imports == "using Foo\nusing Bar"
    assert code_obj.code == "x = 1\ny = 2"


def test_get_code_from_response_without_imports():
    response = "```julia\nx = 1\ny = 2\n```"
    code_obj = get_code_from_response(response)
    assert code_obj.imports == ""
    assert code_obj.code == "x = 1\ny = 2"


def test_get_code_from_response_no_code_block():
    response = "No code block here."
    code_obj = get_code_from_response(response)
    assert code_obj.imports == ""
    assert code_obj.code == ""
