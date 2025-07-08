import os
import tempfile

import pytest

from jutulgpt.state import Code
from jutulgpt.utils import format_code_response, load_lines_from_txt


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
    code = Code(prefix="desc", imports="import A", code="println(1)")
    out = format_code_response(code)
    assert "desc" in out
    assert "import A" in out
    assert "println(1)" in out
    assert "```julia" in out


def test_format_code_response_prefix_only():
    code = Code(prefix="desc", imports="", code="")
    out = format_code_response(code)
    assert out.startswith("Response:\ndesc")
    assert "```julia" not in out


def test_format_code_response_code_only():
    code = Code(prefix="", imports="", code="println(1)")
    out = format_code_response(code)
    assert "println(1)" in out
    assert "```julia" in out


def test_format_code_response_imports_only():
    code = Code(prefix="", imports="import A", code="")
    out = format_code_response(code)
    assert "import A" in out
    assert "```julia" in out
