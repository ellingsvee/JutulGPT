import logging
import os
from dataclasses import asdict
from typing import List

from jutulgpt.config import logging_level
from jutulgpt.state import Code


def load_lines_from_txt(file_path):
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


def format_code_response(code: Code) -> str:
    out = "Response:\n"
    if code.prefix != "":
        out += f"{code.prefix}\n\n"
    if code.imports != "" or code.code != "":
        out += "```julia\n"
        if code.imports != "":
            out += f"{code.imports}\n\n"
        if code.code != "":
            out += f"{code.code}\n"
        out += "```"
    return out


# Configure logger
logger = logging.getLogger("jutulgpt")
logging.basicConfig(level=logging_level, format="%(name)s: %(message)s")

# Set your module's log level
logging.getLogger("jutulgpt").setLevel(logging.DEBUG)

# Suppress overly verbose logs from dependencies
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)  # sometimes used under the hood
logging.getLogger("langchain").setLevel(logging.ERROR)  # if needed


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
