from unittest.mock import MagicMock, patch

import pytest

from jutulgpt.agents import agent, code_gen_chain, get_structured_response
from jutulgpt.state import Code


def test_get_structured_response_success():
    code = Code(prefix="desc", imports="import os", code="print('hi')")
    response = {"structured_response": code}
    result = get_structured_response(response)
    assert isinstance(result, Code)
    assert result.code == "print('hi')"


def test_get_structured_response_missing():
    response = {}
    with pytest.raises(ValueError):
        get_structured_response(response)


# @patch("jutulgpt.agents.agent")
# def test_code_gen_chain_invocation(mock_agent):
#     # Mock the agent to return a dummy response
#     dummy_code = Code(prefix="desc", imports="import os", code="print('hi')")
#     mock_agent.invoke.return_value = {"structured_response": dummy_code}
#     prompt = "Write a hello world program."
#     # code_gen_chain is code_gen_prompt | agent, so we can call it with a string
#     result = code_gen_chain.invoke(prompt)
#     assert "structured_response" in result or isinstance(result, Code)
