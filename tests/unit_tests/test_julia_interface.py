import pytest

from jutulgpt.julia_interface import (
    _split_stacktrace,
    run_string,
)
from jutulgpt.state import CodeBlock


def test_run_string_valid():
    code = "x = 2; y = x^3; y"
    result = run_string(code)
    assert result["error"] is False
    assert result["error_message"] is None
    assert result["error_stacktrace"] is None


def test_run_string_print_output():
    code = 'println("Hello from Julia!")'
    result = run_string(code)
    assert result["error"] is False
    assert result["error_message"] is None
    assert result["error_stacktrace"] is None


def test_run_string_error():
    code = "x = 2; y = ; println(y)"
    result = run_string(code)
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
