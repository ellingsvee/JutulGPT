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
