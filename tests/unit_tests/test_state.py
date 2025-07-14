import pytest

from jutulgpt.state import CodeBlock, State


def test_code_model_fields():
    code = CodeBlock(imports="import os", code="print('hi')")
    assert code.imports == "import os"
    assert code.code == "print('hi')"
    # Test default values
    code2 = CodeBlock()
    assert code2.imports == ""
    assert code2.code == ""
