from langchain_core.documents import Document


def modify_doc_content(doc: Document, new_content: str) -> Document:
    """
    Modify the content of a document.
    """
    doc.page_content = new_content.strip()
    return doc
