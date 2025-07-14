import os
import tempfile

import pytest

from jutulgpt.state import CodeBlock
from jutulgpt.utils import (
    format_code_response,
    load_lines_from_txt,
    split_code_into_lines,
)


def test_load_lines_from_txt_normal():
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write("line1\n\nline2\n   \nline3\n")
        fname = f.name
    lines = load_lines_from_txt(fname)
    assert lines == ["line1", "line2", "line3"]
    os.remove(fname)


def test_load_lines_from_txt_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_lines_from_txt("nonexistent_file.txt")


def test_load_lines_from_txt_empty_file():
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        fname = f.name
    lines = load_lines_from_txt(fname)
    assert lines == []
    os.remove(fname)


def test_load_lines_from_txt_invalid_path():
    with pytest.raises(ValueError):
        load_lines_from_txt("")


def test_format_code_response_all_fields():
    code = CodeBlock(imports="using A", code="println(1)")
    out = format_code_response(code)
    assert "using A" in out
    assert "println(1)" in out
    assert "```julia" in out


def test_format_code_response_prefix_only():
    code = CodeBlock(imports="", code="")
    out = format_code_response(code)
    assert "```julia" not in out


def test_format_code_response_code_only():
    code = CodeBlock(imports="", code="println(1)")
    out = format_code_response(code)
    assert "println(1)" in out
    assert "```julia" in out


def test_format_code_response_imports_only():
    code = CodeBlock(imports="using A", code="")
    out = format_code_response(code)
    assert "using A" in out
    assert "```julia" in out


def test_split_julia_code_into_lines():
    code = """
func(a, b)
func1(
    a = 1,
    c = k({}),
    b = 2,
)
"""
    lines = split_code_into_lines(code)
    assert lines[0] == "func(a, b)"
    assert (
        lines[1]
        in """
func1(
    a = 1,
    c = k({}),
    b = 2,
)
    """
    )
