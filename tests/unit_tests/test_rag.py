from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

import jutulgpt.rag as rag
from jutulgpt.configuration import embedding_model


def test_deduplicate_chunks():
    docs = [
        Document(page_content="A", metadata={}),
        Document(page_content="B", metadata={}),
        Document(page_content="A", metadata={}),
    ]
    deduped = rag._deduplicate_chunks(docs)
    assert len(deduped) == 2
    assert any(doc.page_content == "A" for doc in deduped)
    assert any(doc.page_content == "B" for doc in deduped)


def test_format_examples_groups_and_formats():
    docs = [
        Document(
            page_content="Example 1", metadata={"source": "file1", "heading": "Sec1"}
        ),
        Document(
            page_content="Example 2", metadata={"source": "file1", "heading": "Sec1"}
        ),
        Document(
            page_content="Example 3", metadata={"source": "file2", "heading": "Sec2"}
        ),
    ]
    formatted = rag.format_examples(docs, n=3)
    assert "# From `file1` — Section: `Sec1`" in formatted
    assert "# From `file2` — Section: `Sec2`" in formatted
    assert (
        "Example 1" in formatted
        and "Example 2" in formatted
        and "Example 3" in formatted
    )


def test_format_docs_formats_and_limits():
    docs = [
        Document(page_content="Doc 1", metadata={"Header 1": "A", "source": "f1"}),
        Document(page_content="Doc 2", metadata={"Header 1": "B", "source": "f2"}),
        Document(page_content="Doc 3", metadata={"Header 1": "C", "source": "f3"}),
        Document(page_content="Doc 4", metadata={"Header 1": "D", "source": "f4"}),
    ]
    formatted = rag.format_docs(docs, n=2)
    assert formatted.count("# From") == 2  # Only n=2 docs formatted


#


@patch("jutulgpt.rag.DirectoryLoader")
@patch("jutulgpt.rag._load_or_retrieve_from_storage")
def test_julia_example_indexer_load_and_split(mock_load, mock_loader):
    # Mock loading returns a list of Documents
    doc = Document(
        page_content="# ## Heading\nSome code\n# ## Another Heading\nMore code",
        metadata={"source": "f.jl"},
    )
    mock_load.return_value = [doc]
    indexer = rag.JuliaExampleIndexer(embedding_model=embedding_model)
    docs = indexer.load()
    assert isinstance(docs, list)
    chunks = indexer.split(docs)
    assert isinstance(chunks, list)
    assert all(isinstance(c, Document) for c in chunks)
    # Should split into at least two chunks (one per heading)
    assert len(chunks) >= 2


@patch("jutulgpt.rag.DirectoryLoader")
@patch("jutulgpt.rag._load_or_retrieve_from_storage")
def test_markdown_doc_indexer_load_and_split(mock_load, mock_loader):
    doc = Document(
        page_content="# Heading\nSome text\n## Subheading\nMore text",
        metadata={"source": "f.md"},
    )
    mock_load.return_value = [doc]
    indexer = rag.MarkdownDocIndexer(embedding_model=embedding_model)
    docs = indexer.load()
    assert isinstance(docs, list)
    chunks = indexer.split(docs)
    assert isinstance(chunks, list)
    assert all(isinstance(c, Document) for c in chunks)
    # Should split into at least two chunks (one per heading)
    assert len(chunks) >= 2


@patch("jutulgpt.rag.Chroma")
def test_julia_example_indexer_get_retriever(mock_chroma):
    indexer = rag.JuliaExampleIndexer(embedding_model=embedding_model)
    indexer.split = MagicMock(return_value=[Document(page_content="A", metadata={})])
    indexer.load = MagicMock(return_value=[Document(page_content="A", metadata={})])
    retriever = indexer.get_retriever()
    assert hasattr(retriever, "invoke")


@patch("jutulgpt.rag.Chroma")
def test_markdown_doc_indexer_get_retriever(mock_chroma):
    indexer = rag.MarkdownDocIndexer(embedding_model=embedding_model)
    indexer.split = MagicMock(return_value=[Document(page_content="A", metadata={})])
    indexer.load = MagicMock(return_value=[Document(page_content="A", metadata={})])
    retriever = indexer.get_retriever()
    assert hasattr(retriever, "invoke")
