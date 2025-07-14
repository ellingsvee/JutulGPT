from unittest.mock import MagicMock, patch

import pytest
from langchain.schema import Document
from langchain_core.messages import AIMessage, HumanMessage

from jutulgpt.nodes.generate_response import generate_response
from jutulgpt.state import State


@pytest.fixture
def dummy_state():
    return State(
        messages=[HumanMessage(content="Hello")],
        error=False,
        error_message="",
        is_last_step=False,
        iterations=0,
    )


@pytest.fixture
def dummy_config():
    return {}


# @patch("jutulgpt.nodes.generate_response.load_chat_model")
# @patch("jutulgpt.nodes.generate_response.Configuration")
# def test_generate_response_normal(
#     mock_config_cls, mock_load_chat_model, dummy_state, dummy_config
# ):
#     mock_config = MagicMock()
#     mock_config.model = "test-model"
#     mock_config.system_prompt = "system"
#     mock_config_cls.from_runnable_config.return_value = mock_config

#     mock_model = MagicMock()
#     mock_model.bind_tools.return_value = mock_model
#     mock_model.invoke.return_value = AIMessage(content="Hi!")
#     mock_model.__call__ = MagicMock(return_value=0)
#     mock_load_chat_model.return_value = mock_model

#     result = generate_response(dummy_state, dummy_config)
#     assert "messages" in result
#     assert isinstance(result["messages"][0], AIMessage)
#     assert result["messages"][0].content == "Hi!"
