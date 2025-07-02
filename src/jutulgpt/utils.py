import logging
import os

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
    return f"{code.prefix}\n\n```julia\n{code.imports}\n\n{code.code}\n```"


# Configure logger
logger = logging.getLogger("jutulgpt")
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

# Set your module's log level
logging.getLogger("jutulgpt").setLevel(logging.INFO)

# Suppress overly verbose logs from dependencies
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)  # sometimes used under the hood
logging.getLogger("langchain").setLevel(logging.WARNING)  # if needed
