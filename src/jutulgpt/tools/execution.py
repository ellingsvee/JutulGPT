"""Tools for executing code and terminal commands."""

import os
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from jutulgpt.cli import colorscheme, print_to_console


@tool
def execute_julia_code(code: str, working_directory: Optional[str] = None) -> str:
    """
    Execute Julia code in a temporary file and return the output.

    Args:
        code: The Julia code to execute
        working_directory: Optional working directory to run the code in

    Returns:
        str: The output from executing the code (stdout and stderr combined)
    """
    if working_directory is None:
        working_directory = os.getcwd()

    # Create a temporary Julia file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jl", delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Execute the Julia code
        result = subprocess.run(
            ["julia", temp_file],
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )

        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        if result.returncode != 0:
            output += f"EXIT CODE: {result.returncode}\n"

        return (
            output.strip()
            if output.strip()
            else "Code executed successfully with no output."
        )

    except subprocess.TimeoutExpired:
        return "ERROR: Code execution timed out after 60 seconds."
    except Exception as e:
        return f"ERROR: Failed to execute code: {str(e)}"
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except:
            pass


@tool
def execute_terminal_command(
    command: str, working_directory: Optional[str] = None
) -> str:
    """
    Execute a terminal command and return the output.

    Args:
        command: The command to execute
        working_directory: Optional working directory to run the command in

    Returns:
        str: The output from executing the command (stdout and stderr combined)
    """
    if working_directory is None:
        working_directory = os.getcwd()

    try:
        # Execute the command
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=60,  # 60 second timeout
        )

        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        if result.returncode != 0:
            output += f"EXIT CODE: {result.returncode}\n"

        return (
            output.strip()
            if output.strip()
            else "Command executed successfully with no output."
        )

    except subprocess.TimeoutExpired:
        return "ERROR: Command execution timed out after 60 seconds."
    except Exception as e:
        return f"ERROR: Failed to execute command: {str(e)}"


@tool
def list_directory_contents(directory_path: str) -> str:
    """
    List the contents of a directory.

    Args:
        directory_path: Path to the directory to list

    Returns:
        str: Directory contents listing
    """
    try:
        if not os.path.exists(directory_path):
            return f"ERROR: Directory {directory_path} does not exist."

        if not os.path.isdir(directory_path):
            return f"ERROR: {directory_path} is not a directory."

        contents = os.listdir(directory_path)
        if not contents:
            return f"Directory {directory_path} is empty."

        # Sort and format the contents
        contents.sort()
        formatted_contents = []
        for item in contents:
            item_path = os.path.join(directory_path, item)
            if os.path.isdir(item_path):
                formatted_contents.append(f"[DIR]  {item}/")
            else:
                formatted_contents.append(f"[FILE] {item}")

        return f"Contents of {directory_path}:\n" + "\n".join(formatted_contents)

    except Exception as e:
        return f"ERROR: Failed to list directory contents: {str(e)}"


@tool
def get_working_directory() -> str:
    """
    Get the current working directory.

    Returns:
        str: The current working directory path
    """
    return os.getcwd()


@tool
def change_working_directory(directory_path: str) -> str:
    """
    Change the working directory.

    Args:
        directory_path: Path to the directory to change to

    Returns:
        str: Confirmation message or error
    """
    try:
        if not os.path.exists(directory_path):
            return f"ERROR: Directory {directory_path} does not exist."

        if not os.path.isdir(directory_path):
            return f"ERROR: {directory_path} is not a directory."

        os.chdir(directory_path)
        return f"Successfully changed working directory to: {os.getcwd()}"

    except Exception as e:
        return f"ERROR: Failed to change directory: {str(e)}"


@tool
def create_julia_workspace(task_name: str, base_directory: Optional[str] = None) -> str:
    """
    Create a simple workspace with a single Julia file.

    Args:
        task_name: Name of the task
        base_directory: Optional base directory to create workspace in

    Returns:
        str: Path to the created Julia file
    """
    if base_directory is None:
        base_directory = os.getcwd()

    # Simple sanitization
    safe_task_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", task_name.lower())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    workspace_dir = Path(base_directory) / "jutulgpt_workspaces"
    workspace_dir.mkdir(parents=True, exist_ok=True)

    julia_file = workspace_dir / f"{safe_task_name}_{timestamp}.jl"

    print_to_console(
        text=f"Creating Julia workspace for task '{task_name}' at {julia_file}",
        title="Tool: Create Julia Workspace",
        border_style=colorscheme.message,
    )

    try:
        with open(julia_file, "w") as f:
            f.write(f"# {task_name}\n")
            f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        return str(julia_file)

    except Exception as e:
        return f"ERROR: Failed to create workspace: {str(e)}"


@tool
def write_julia_code_to_file(code: str, file_path: str, append: bool = False) -> str:
    """
    Write Julia code to a file.

    Args:
        code: The Julia code to write
        file_path: Path to the Julia file
        append: Whether to append to existing file or overwrite

    Returns:
        str: Confirmation message or error
    """
    print_to_console(
        text=f"Writing Julia code to {file_path} (append={append})",
        title="Tool: Write Julia Code to File",
        border_style=colorscheme.message,
    )

    try:
        mode = "a" if append else "w"
        with open(file_path, mode) as f:
            if append:
                f.write("\n")
            f.write(code)
            if not code.endswith("\n"):
                f.write("\n")

        action = "appended to" if append else "written to"
        return f"Successfully {action} {file_path}"

    except Exception as e:
        return f"ERROR: Failed to write to file: {str(e)}"


@tool
def execute_julia_file(file_path: str) -> str:
    """
    Execute a Julia file and return the output.

    Args:
        file_path: Path to the Julia file to execute

    Returns:
        str: Execution output and exit code
    """
    print_to_console(
        text=f"Executing Julia file: {file_path}",
        title="Tool: Execute Julia File",
        border_style=colorscheme.warning,
    )
    try:
        if not os.path.exists(file_path):
            return f"ERROR: File {file_path} does not exist"

        result = subprocess.run(
            ["julia", file_path], capture_output=True, text=True, timeout=30
        )

        output = f"=== Execution of {file_path} ===\n"

        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"

        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"

        output += f"EXIT CODE: {result.returncode}\n"

        print_to_console(
            text=output.strip(),
            title="Execution Result",
            border_style=colorscheme.success
            if result.returncode == 0
            else colorscheme.error,
        )

        return output

    except subprocess.TimeoutExpired:
        return f"ERROR: Execution of {file_path} timed out after 30 seconds"
    except Exception as e:
        return f"ERROR: Failed to execute {file_path}: {str(e)}"
