"""Utility & helper functions."""

import os
from dataclasses import asdict
from typing import List, Union

from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from jutulgpt.state import CodeBlock


def load_lines_from_txt(file_path: str) -> List[str]:
    """
    Load lines from a text file, stripping whitespace and ignoring empty lines.

    Args:
        file_path (str): Path to the text file.

    Returns:
        list: List of non-empty, stripped lines from the file.
    """
    if not file_path:
        raise ValueError("File path cannot be empty.")
    if not isinstance(file_path, str):
        file_path = str(file_path)
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        raise FileNotFoundError(
            f"The file at {file_path} does not exist. Current working directory is {os.getcwd()}."
        )
    except IOError as e:
        raise IOError(
            f"An error occurred while reading the file at {file_path}: {e}"
        ) from e
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}") from e


def format_code_response(code: CodeBlock) -> str:
    out = ""
    if code.imports != "" or code.code != "":
        out += "```julia\n"
        if code.imports != "":
            out += f"{code.imports}\n\n"
        if code.code != "":
            out += f"{code.code}\n"
        out += "```"
    return out


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def load_chat_model(fully_specified_name: str) -> BaseChatModel:
    """Load a chat model from a fully specified name.

    Args:
        fully_specified_name (str): String in the format 'provider/model'.
    """
    provider, model = fully_specified_name.split("/", maxsplit=1)
    return init_chat_model(model, model_provider=provider, temperature=0.1)


def load_embedding_model(
    embedding_model_name: str,
) -> Union[OpenAIEmbeddings, OllamaEmbeddings]:
    """Instantiate the embedding model based on the config."""

    provider, model = embedding_model_name.split("/", maxsplit=1)
    if provider == "openai":
        return OpenAIEmbeddings(model=model)
    elif provider == "ollama":
        return OllamaEmbeddings(model=model)

    else:
        raise ValueError(f"Unsupported embedding model: {embedding_model_name}")


def get_tool_message(messages: List, n_last=2, print=False):
    """
    Extract the most recent tool message from a list of messages.

    Args:
        messages (list): List of messages.
        n_last (int): Number of last messages to consider for finding the tool message.

    Returns:
        str: The content of the most recent tool message, or None if no tool message is found.
    """

    # for message in reversed(messages):
    for message in messages[-n_last:]:
        if message.type == "tool":
            if print:
                message.pretty_print()
            return message
    return None


def state_to_dict(state, remove_keys: List[str] = []) -> dict:
    state_dict = asdict(state)
    for key in remove_keys:
        state_dict.pop(key, None)
    return state_dict


def deduplicate_document_chunks(chunks: List[Document]) -> List[Document]:
    seen = set()
    deduped = []
    for doc in chunks:
        content = doc.page_content.strip()
        if content not in seen:
            seen.add(content)
            deduped.append(doc)
    return deduped


def split_code_into_lines(code: str):
    """
    Splits Julia code into blocks based solely on bracket balance:
    (), [], {}. Multi-line constructs are supported without relying
    on language-specific keywords.
    """
    lines = code.splitlines()
    blocks = []
    current_block = []
    parens = brackets = braces = 0

    for line in lines:
        stripped = line.strip()
        if not stripped and not current_block:
            continue  # Skip empty lines outside a block

        # Update bracket counts
        parens += line.count("(") - line.count(")")
        brackets += line.count("[") - line.count("]")
        braces += line.count("{") - line.count("}")

        current_block.append(line)

        # If all brackets are balanced, this is a complete block
        if parens == 0 and brackets == 0 and braces == 0:
            blocks.append("\n".join(current_block))
            current_block = []

    # In case something is left unbalanced (e.g., trailing incomplete block)
    if current_block:
        blocks.append("\n".join(current_block))

    return blocks
