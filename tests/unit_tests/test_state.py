import pytest

from jutulgpt.state import CodeBlock, State


def test_code_block_fields():
    code = CodeBlock(imports="import os", code="print('hi')")
    assert code.imports == "import os"
    assert code.code == "print('hi')"
    # Test default values
    code2 = CodeBlock()
    assert code2.imports == ""
    assert code2.code == ""


def test_code_block_get_full_code_within_context():
    code = CodeBlock(imports="import os", code="print('hi')")
    full_code = code.get_full_code(within_julia_context=True)
    assert full_code == "```julia\nimport os\nprint('hi')\n```"


def test_code_block_get_full_code_without_context():
    code = CodeBlock(imports="import os", code="print('hi')")
    full_code = code.get_full_code(within_julia_context=False)
    assert full_code == "import os\nprint('hi')"
