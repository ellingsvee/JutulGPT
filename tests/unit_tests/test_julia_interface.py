import pytest

from jutulgpt.julia_interface import run_string


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
