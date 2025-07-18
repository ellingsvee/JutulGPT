from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from jutulgpt.human_in_the_loop.response_on_rag import response_on_rag


@pytest.fixture
def docs():
    return [
        Document(page_content="Doc1", metadata={"id": 1}),
        Document(page_content="Doc2", metadata={"id": 2}),
    ]


def dummy_get_file_source(doc, for_ui_printing=False):
    return f"file_{doc.metadata['id']}"


def dummy_get_section_path(doc, for_ui_printing=False):
    return f"section_{doc.metadata['id']}"


def dummy_format_doc(doc):
    return doc.page_content


@patch("jutulgpt.human_in_the_loop.response_on_rag.modify_doc_content")
@patch("jutulgpt.human_in_the_loop.response_on_rag.interrupt")
def test_response_on_rag_edit(mock_interrupt, mock_modify, docs):
    # Simulate user editing the first doc and deleting the second
    mock_interrupt.return_value = [
        {
            "type": "edit",
            "args": {
                "args": {
                    "file_1 - section_1": "Modified Doc1",
                    "file_2 - section_2": "",
                }
            },
        }
    ]
    mock_modify.side_effect = lambda doc, new_content: Document(
        page_content=new_content, metadata=doc.metadata
    )
    result = response_on_rag(
        docs.copy(),
        dummy_get_file_source,
        dummy_get_section_path,
        dummy_format_doc,
    )
    assert len(result) == 1
    assert result[0].page_content == "Modified Doc1"


@patch("jutulgpt.human_in_the_loop.response_on_rag.interrupt")
def test_response_on_rag_ignore(mock_interrupt, docs):
    # Simulate user ignoring the edit
    mock_interrupt.return_value = [{"type": "ignore"}]
    result = response_on_rag(
        docs.copy(),
        dummy_get_file_source,
        dummy_get_section_path,
        dummy_format_doc,
    )
    assert len(result) == 2
    assert result[0].page_content == "Doc1"
    assert result[1].page_content == "Doc2"


def test_response_on_rag_empty_docs():
    # Should return empty list if no docs
    result = response_on_rag(
        [],
        dummy_get_file_source,
        dummy_get_section_path,
        dummy_format_doc,
    )
    assert result == []
