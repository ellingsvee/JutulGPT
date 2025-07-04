import os
import pickle

from langchain_chroma import Chroma
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from jutulgpt.config import embedding
from jutulgpt.utils import logger

persist_directory = "./chroma_docs_dir"
loaded_docs_path = "./src/jutulgpt/rag_sources/loaded_docs.pkl"
if os.path.exists(loaded_docs_path):
    logger.info("Loading existing loaded_docs from disk.")
    with open(loaded_docs_path, "rb") as f:
        loaded = pickle.load(f)
else:
    logger.info("loaded_docs not found. Generating new one.")
    loader_docs = DirectoryLoader(
        path="./src/jutulgpt/rag_sources/jutuldarcy_docs/man/",
        glob="**/*.md",
        show_progress=True,
        loader_cls=UnstructuredMarkdownLoader,
    )

    loaded = loader_docs.load()

    with open(loaded_docs_path, "wb") as f:
        pickle.dump(loaded, f)

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
splits = splitter.split_documents(loaded)

vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embedding,
    persist_directory=persist_directory,
)

docs_retriever = vectorstore.as_retriever()


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)
