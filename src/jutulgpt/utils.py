"""Utility & helper functions."""

import os
import re
from dataclasses import asdict
from typing import List

from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from jutulgpt.state import CodeBlock, State


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
    """
    Format a CodeBlock object as a Markdown Julia code block string.

    Args:
        code (CodeBlock): The code block containing imports and code.

    Returns:
        str: Markdown-formatted Julia code block, or empty string if no code/imports.
    """
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
    match provider:
        case "openai":
            return init_chat_model(model, model_provider=provider, temperature=0.1)
        case "ollama":
            return init_chat_model(
                model, model_provider=provider, temperature=0.1, reasoning=True
            )
        case _:
            raise ValueError(f"Unsupported chat model provider: {provider}")


def get_tool_message(messages: List, n_last=2, print=False):
    """
    Extract the most recent tool message from the last n messages.

    Args:
        messages (list): List of message objects.
        n_last (int): Number of last messages to consider.
        print (bool): If True, pretty print the found message.

    Returns:
        The most recent tool message object, or None if not found.
    """
    for message in messages[-n_last:]:
        if message.type == "tool":
            if print:
                message.pretty_print()
            return message
    return None


def state_to_dict(state, remove_keys: List[str] = []) -> dict:
    """
    Convert a State object to a dictionary, optionally removing specified keys.

    Args:
        state: The State object to convert.
        remove_keys (List[str]): Keys to remove from the resulting dictionary.

    Returns:
        dict: Dictionary representation of the state with specified keys removed.
    """
    state_dict = asdict(state)
    for key in remove_keys:
        state_dict.pop(key, None)
    return state_dict


def deduplicate_document_chunks(chunks: List[Document]) -> List[Document]:
    """
    Remove duplicate Document chunks based on their page content.

    Args:
        chunks (List[Document]): List of Document objects.

    Returns:
        List[Document]: List of unique Document objects.
    """
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
    Split Julia code into blocks based on bracket balance ((), [], {}).
    Multi-line constructs are supported without relying on language-specific keywords.

    Args:
        code (str): Julia code as a string.

    Returns:
        list: List of code blocks as strings, each with balanced brackets.
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


def _get_code_string_from_response(response: str) -> str:
    """
    Extract Julia code from a Markdown-style Julia code block in a response string.

    Args:
        response (str): The response string containing a Markdown Julia code block.

    Returns:
        str: The extracted Julia code, or an empty string if not found.
    """
    match = re.search(r"```julia\s*([\s\S]*?)```", response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def get_code_from_response(response: str) -> CodeBlock:
    """
    Extract Julia code and import statements from a Markdown code block in a response string.

    Args:
        response (str): The response string containing a Markdown Julia code block.

    Returns:
        CodeBlock: An object containing separated imports and code.
    """
    code_str = _get_code_string_from_response(response)
    if not code_str:
        return CodeBlock(imports="", code="")

    import_lines = []
    code_lines = []
    for line in code_str.splitlines():
        if line.strip().startswith(("using ")):
            import_lines.append(line.strip())
        else:
            code_lines.append(line)

    return CodeBlock(
        imports="\n".join(import_lines), code="\n".join(code_lines).strip()
    )


def get_last_code_response(state: State) -> CodeBlock:
    """
    Get the last AI-generated code response from the state as a CodeBlock.

    Args:
        state (State): The current State object containing messages.

    Returns:
        CodeBlock: The extracted code block from the last AI message, or empty if not found.
    """
    last_message = state.messages[-1]

    # Include the human in case the human-in-the-loop updates the generated code.

    print("Inside: get_last_code_response")
    print(f"last_message.type: {last_message.type}")
    if last_message.type == "ai" or last_message.type == "human":
        last_message_content = last_message.content
        print(f"last_message_content: {last_message_content}")
    else:
        last_message_content = ""
    code_block = get_code_from_response(last_message_content)
    return code_block
