import os
import re
import subprocess
import tempfile
import time
from typing import Union


def run_code_tempfile(code: str, project_dir: str | None = None):
    """
    Takes in a code string, writes it to a temporary file, and runs it in Julia using the subprocess module.
    """
    if project_dir is None:
        project_dir = os.getcwd()

    # Create a temporary file with Julia code in the project directory
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jl", delete=False, encoding="utf-8", dir=project_dir
    ) as temp_file:
        temp_file.write(code)
        temp_file.flush()  # Ensure content is written to disk
        temp_file_path = temp_file.name

    try:
        # Run the Julia file with the project activated
        result = subprocess.run(
            ["julia", f"--project={project_dir}", temp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_dir,  # Set working directory to project directory
        )
        print(f"Julia exit code: {result.returncode}")
        return result.stdout, result.stderr
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass  # File might already be deleted


def run_julia_file(code: str, julia_file_name: str, project_dir: str | None = None):
    assert julia_file_name.endswith(".jl"), "julia_file_name must end with .jl"

    if project_dir is None:
        project_dir = os.getcwd()

    # Create a temporary file with Julia code in the project directory
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jl", delete=False, encoding="utf-8", dir=project_dir
    ) as temp_file:
        temp_file.write(code)
        temp_file.flush()  # Ensure content is written to disk
        temp_file_path = temp_file.name

    try:
        # Run the Julia file with the project activated
        # result = subprocess.run(
        #     ["julia", f"--project={project_dir}", temp_file_path],
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     text=True,
        #     cwd=project_dir,  # Set working directory to project directory
        # )
        julia_script = os.path.join(
            project_dir, "src", "jutulgpt", "julia", julia_file_name
        )
        # print(f"Running lint script: {julia_script}")
        result = subprocess.run(
            [
                "julia",
                f"--project={project_dir}",
                julia_script,
                project_dir,
                temp_file_path,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_dir,
        )
        # print(f"Julia exit code: {result.returncode}")
        return result.stdout, result.stderr
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass  # File might already be deleted


def run_code_string_direct(code: str, project_dir: str | None = None):
    """
    Alternative approach: Run Julia code directly using -e flag instead of temporary file.
    """
    if project_dir is None:
        project_dir = os.getcwd()

    try:
        result = subprocess.run(
            ["julia", f"--project={project_dir}", "-e", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_dir,
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", f"Error running Julia: {e}"


def _split_stacktrace(msg: str):
    """
    Split a Julia error message into the main error message and the stacktrace.

    Args:
        msg (str): The full error message string from Julia.

    Returns:
        tuple: (main error message, stacktrace) if found, otherwise (msg, None)
    """
    marker = "\nStacktrace:\n"
    if marker in msg:
        pre_stack, stack = msg.split(marker, 1)
        return pre_stack.strip(), stack.strip()
    else:
        # Handle the case where "Stacktrace" is part of the string but not split cleanly
        m = re.search(r"(.*?)(\nStacktrace:\n.*)", msg, re.DOTALL)
        if m:
            return m.group(1).strip(), m.group(2).replace("Stacktrace:\n", "").strip()
    return msg.strip(), None


def _filter_stacktrace(stack: str, exclude_patterns=None) -> Union[str, None]:
    """
    Filter out lines in a Julia stacktrace that are internal to PythonCall, JlWrap, or other irrelevant internals.

    Args:
        stack (str): The full stacktrace string from Julia.
        exclude_patterns (list, optional): List of regex patterns to exclude from the stacktrace.

    Returns:
        str or None: The filtered stacktrace, or None if all lines are excluded.
    """
    if exclude_patterns is None:
        exclude_patterns = [r"PythonCall", r"JlWrap", r"juliacall", r"pyjlmodule_seval"]

    lines = stack.splitlines()
    keep_lines = []
    for line in lines:
        if not any(re.search(pattern, line) for pattern in exclude_patterns):
            keep_lines.append(line)
    return "\n".join(keep_lines) if keep_lines else None


def get_error_message(result) -> str:
    """
    Format the error message and stacktrace from a result dictionary returned by run_string.

    Args:
        result (dict): The result dictionary from run_string.

    Returns:
        str: The formatted error message including stacktrace if available.
    """
    out_string = f"{result['error_message']}"
    if result["error_stacktrace"] is not None:
        out_string += f"\n\nStacktrace:\n{result['error_stacktrace']}"
    return out_string


def run_code(code: str) -> dict:
    start_time = time.time()
    stdout, stderr = run_code_string_direct(code=code)
    end_time = time.time()

    if stderr:
        error_message, error_stacktrace = _split_stacktrace(stderr)

        result = {
            "output": stdout,
            "error": True,
            "error_message": error_message,
            "error_stacktrace": error_stacktrace,
            "runtime": end_time - start_time,
        }
        return result

    result = {
        "output": stdout,
        "error": False,
        "error_message": "",
        "error_stacktrace": "",
        "runtime": end_time - start_time,
    }
    return result
