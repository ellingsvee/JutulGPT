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
    provider, model = get_provider_and_model(fully_specified_name)
    match provider:
        case "openai":
            return init_chat_model(
                model,
                model_provider=provider,
                temperature=0.1,
            )
        case "ollama":
            print(f"Inside the Ollama provider. Loading {model}")
            # Resoning models need reasoning=True to hide the thinking, but this fails for non-reasoning models.
            if model == "qwen3:14b":  # WARNING: This is VERY bad practice!
                return init_chat_model(
                    model,
                    model_provider=provider,
                    temperature=0.1,
                    reasoning=True,
                )
            else:
                return init_chat_model(
                    model,
                    model_provider=provider,
                    temperature=0.1,
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


def get_last_code_response_2(messages: List) -> CodeBlock:
    """
    Get the last AI-generated code response from the state as a CodeBlock.

    Args:
        state (State): The current State object containing messages.

    Returns:
        CodeBlock: The extracted code block from the last AI message, or empty if not found.
    """
    last_message = messages[-1]

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


def _get_relevant_part_of_file_source(source: str, relevant_doc_name: str = "rag"):
    """
    Remove the part of the soure up to and including the relevant_doc_name.
    """
    idx = source.find(f"/{relevant_doc_name}/")
    if idx != -1:
        source = source[idx + len("/rag/") :]
    return source


def get_file_source(
    doc: Document, for_ui_printing: bool = False, only_relevant_part: bool = True
) -> str:
    file_source = doc.metadata.get("source", "Unknown Document")
    if only_relevant_part:
        file_source = _get_relevant_part_of_file_source(file_source)
    if for_ui_printing:
        return f"{file_source}"
    return file_source


def get_provider_and_model(name: str) -> tuple[str, str]:
    """
    Get the provider and name from a string on the format 'provider/model'.
    """
    provider, model = name.split("/", maxsplit=1)
    return provider, model


def check_for_package_install(code_block: CodeBlock) -> bool:
    not_allowed = [
        "using Pkg",  # Pkg is used to install packages, which is not allowed
        "Pkg.add",  # Pkg.add is used to install packages, which is not allowed
        "Pkg.update",  # Pkg.update is used to update packages, which is not allowed
        "Pkg.instantiate",  # Pkg.instantiate is used to install dependencies, which is not allowed
    ]
    if any(item in code_block.imports for item in not_allowed):
        return True
    if any(item in code_block.code for item in not_allowed):
        return True
    return False


def remove_plotting(code: str) -> str:
    """
    Remove GLMakie usage and plotting code from Julia code blocks.
    F.ex:
    - Removes 'using GLMakie' or 'using ... GLMakie ...' from using statements.
    - Removes lines that define or use 'fig', 'ax', or call 'lines!'.
    - Removes lines that are just 'fig' (returning the figure).
    """
    # TODO: This is a very naive implementation, it should be improved.
    remove_functions = [
        "fig",
        "plt",
        "ax",
        "scatter",
        "Colorbar",
        "Axis",
        "lines",
        "plot_reservoir",
        "plot_well_results",
        "plot_reservoir_measurables",
        "plot_reservoir_simulation_result",
        "plot_well!",
        "myplot",
        "plot_cell_data",
        "plot_mesh_edges",
        "plot_mesh",
        "plot_co2_inventory",
        "println",  # To avoid printing to terminal
    ]

    # lines = code.splitlines()
    lines = split_code_into_lines(code)
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # Remove 'using GLMakie' or 'using ... GLMakie ...'
        if stripped.startswith("using"):
            # Remove 'GLMakie' from the using statement
            # Handles cases like: using JutulDarcy, GLMakie, Jutul;
            # and: using GLMakie
            line = re.sub(r",?\s*GLMakie,?", "", line)
            # Remove trailing/leading commas and extra spaces
            line = re.sub(r"using\s*,", "using ", line)
            line = re.sub(r",\s*;", ";", line)
            # If nothing left after 'using', skip the line
            if re.match(r"^\s*using\s*;?\s*$", line):
                continue
            # If the line is now empty, skip it
            if not line.strip():
                continue
        # Remove lines that define or use fig, ax, or call lines!
        if stripped == "fig":
            continue

        if any(func in stripped for func in remove_functions):
            continue
        new_lines.append(line)
    return "\n".join(new_lines)


def shorten_first_argument(code: str, simulation_functions: List[str]) -> str:
    """
    For each simulation function, append '[1:1]' to the first argument of the function call.
    E.g., sim_func_1(foo, bar) -> sim_func_1(foo[1:1], bar)
    """

    for func in simulation_functions:
        # Match the function call and capture the first argument
        pattern = rf"({func}\s*\()\s*([^,)\s]+)(.*?\))"

        def replacer(match):
            before = match.group(1)
            first_arg = match.group(2)
            after = match.group(3)
            return f"{before}{first_arg}[1:1]{after}"

        code = re.sub(pattern, replacer, code, flags=re.DOTALL)

    return code


def replace_case(code: str, case_name: str, simulation_functions: List[str]) -> str:
    """
    Replacing the 'case' with 'case[1:1]'.
    """
    for func in simulation_functions:
        # Match 'case' as a whole word in the argument list
        pattern = rf"({func}\s*\(.*?)(\b{case_name}\b)(.*?\))"

        def replacer(match):
            before = match.group(1)
            after = match.group(3)
            return f"{before}{case_name}[1:1]{after}"

        code = re.sub(pattern, replacer, code, flags=re.DOTALL)
    return code
