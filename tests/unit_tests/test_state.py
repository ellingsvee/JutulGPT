import pytest

from jutulgpt.state import Code, State


def test_code_model_fields():
    code = Code(imports="import os", code="print('hi')")
    assert code.imports == "import os"
    assert code.code == "print('hi')"
    # Test default values
    code2 = Code()
    assert code2.imports == ""
    assert code2.code == ""
