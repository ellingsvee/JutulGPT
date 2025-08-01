import multiprocessing as mp
import re
import traceback
from typing import Union

from juliacall import JuliaError


class JuliaSubprocessJuliaError(JuliaError):
    """
    Exception raised when a JuliaError occurs in the subprocess during Julia code execution.

    Attributes:
        message (str): The error message from Julia.
        traceback_str (str): The Julia stacktrace, if available.
    """

    def __init__(self, message, traceback_str):
        super().__init__(message)
        self.traceback_str = traceback_str


class JuliaSubprocessOtherError(Exception):
    """
    Exception raised for non-Julia errors occurring in the subprocess during Julia code execution.

    Attributes:
        message (str): The error message from the Python subprocess.
        traceback_str (str): The Python traceback string.
    """

    def __init__(self, message, traceback_str):
        super().__init__(message)
        self.traceback_str = traceback_str


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


def _run_julia_code(code_string, return_queue, capture_output=False):
    """
    Helper function to execute Julia code in a subprocess and return the result or error via a queue.

    Args:
        code_string (str): The Julia code to execute.
        return_queue (multiprocessing.Queue): Queue to put the result or error information.
        capture_output (bool): If True, capture stdout/stderr as string; if False, suppress output.
    """
    try:
        from juliacall import Main as jl_sub

        if capture_output:
            # Use a more robust approach with temporary files
            capture_setup_code = """
            # Store original streams
            original_stdout = stdout
            original_stderr = stderr
            
            # Create temporary files for capturing
            stdout_tmpfile = tempname() * ".out"
            stderr_tmpfile = tempname() * ".err"
            
            # Open files and redirect
            stdout_file = open(stdout_tmpfile, "w")
            stderr_file = open(stderr_tmpfile, "w")
            redirect_stdout(stdout_file)
            redirect_stderr(stderr_file)
            
            # Store file info for cleanup
            _capture_stdout_file = stdout_file
            _capture_stderr_file = stderr_file
            _capture_stdout_path = stdout_tmpfile
            _capture_stderr_path = stderr_tmpfile
            """
            jl_sub.seval(capture_setup_code)
        else:
            # Suppress Julia output by redirecting stdout and stderr to devnull
            # This prevents print statements and other output from being displayed
            suppression_code = """
            original_stdout = stdout
            original_stderr = stderr
            redirect_stdout(devnull)
            redirect_stderr(devnull)
            """
            jl_sub.seval(suppression_code)

        try:
            # Execute the user code
            jl_sub.seval(code_string)
        finally:
            if capture_output:
                # Get the captured output and restore stdout/stderr
                capture_retrieval_code = """
                # Restore streams first
                redirect_stdout(original_stdout)
                redirect_stderr(original_stderr)
                
                # Close the files
                close(_capture_stdout_file)
                close(_capture_stderr_file)
                
                # Read the content from files
                stdout_content = isfile(_capture_stdout_path) ? read(_capture_stdout_path, String) : ""
                stderr_content = isfile(_capture_stderr_path) ? read(_capture_stderr_path, String) : ""
                
                # Clean up temporary files
                try
                    rm(_capture_stdout_path)
                    rm(_capture_stderr_path)
                catch
                    # Ignore cleanup errors
                end
                
                (stdout_content, stderr_content)
                """
                try:
                    output_result = jl_sub.seval(capture_retrieval_code)
                    stdout_content, stderr_content = output_result
                except Exception:
                    # Fallback: if capture fails, return empty strings
                    stdout_content, stderr_content = "", ""

                return_queue.put(
                    (
                        True,
                        {"stdout": str(stdout_content), "stderr": str(stderr_content)},
                    )
                )
            else:
                # Restore original stdout and stderr
                restoration_code = """
                redirect_stdout(original_stdout)
                redirect_stderr(original_stderr)
                """
                jl_sub.seval(restoration_code)
                return_queue.put((True, None))

    except JuliaError as e:
        tb = traceback.format_exc()
        msg = str(e)
        pre_stack, stack = _split_stacktrace(msg)
        return_queue.put(
            (
                False,
                {
                    "type": "JuliaError",
                    "message": pre_stack,
                    "jl_stacktrace": stack,
                    "traceback": tb,
                },
            )
        )
    except Exception as e:
        tb = traceback.format_exc()
        return_queue.put(
            (False, {"type": "OtherError", "message": str(e), "traceback": tb})
        )


def jl_eval_in_subprocess(code_string, timeout=30, capture_output=False):
    """
    Execute Julia code in a separate subprocess for isolation and error handling.

    Args:
        code_string (str): The Julia code to execute.
        timeout (int, optional): Maximum time in seconds to allow for execution.
        capture_output (bool, optional): If True, capture and return stdout/stderr; if False, suppress output.

    Returns:
        dict or None: If capture_output=True, returns dict with 'stdout' and 'stderr' keys.
                     If capture_output=False, returns None on success.

    Raises:
        JuliaSubprocessJuliaError: If a JuliaError occurs in the subprocess.
        JuliaSubprocessOtherError: If a non-Julia error occurs in the subprocess.
        TimeoutError: If the execution exceeds the timeout.
    """
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_run_julia_code, args=(code_string, q, capture_output))
    p.start()

    try:
        p.join(timeout)

        if p.is_alive():
            p.terminate()
            p.join()  # Wait for termination to complete
            raise TimeoutError("Julia code timed out.")

        # Check if the queue has a result (subprocess might have crashed)
        if q.empty():
            raise RuntimeError("Subprocess finished but did not return a result.")

        success, result = q.get()
        if success:
            return result  # Will be None for suppressed output, or dict with stdout/stderr for captured output
        else:
            if result["type"] == "JuliaError":
                if p.is_alive():
                    p.terminate()
                p.join()  # Always wait for process to finish

                raise JuliaSubprocessJuliaError(
                    result["message"], result.get("jl_stacktrace")
                )
            else:
                if p.is_alive():
                    p.terminate()
                p.join()  # Always wait for process to finish

                raise JuliaSubprocessOtherError(result["message"], result["traceback"])
    finally:
        # Ensure subprocess is always cleaned up
        if p.is_alive():
            p.terminate()
        p.join()  # Always wait for process to finish


def run_string(code: str, capture_output=False):
    """
    Execute a Julia code string in a subprocess and return the result or error details.

    Args:
        code (str): The Julia code to execute.
        capture_output (bool, optional): If True, capture stdout/stderr; if False, suppress output.

    Returns:
        dict: A dictionary with keys 'error', 'error_message', 'error_stacktrace',
              and optionally 'stdout' and 'stderr' if capture_output=True.
    """
    try:
        result_data = jl_eval_in_subprocess(code, capture_output=capture_output)

        result = {
            "error": False,
            "error_message": None,
            "error_stacktrace": None,
        }

        # Add output data if it was captured
        if capture_output and result_data is not None:
            result["stdout"] = result_data.get("stdout", "")
            result["stderr"] = result_data.get("stderr", "")

        return result

    # Handle Julia errors raised from within the subprocess
    except JuliaSubprocessJuliaError as e:
        filtered_stack = (
            _filter_stacktrace(e.traceback_str) if e.traceback_str else None
        )

        error_message = str(e)
        result = {
            "error": True,
            "error_message": error_message,
            "error_stacktrace": filtered_stack,
        }

        # Add empty output fields if capture was requested
        if capture_output:
            result["stdout"] = ""
            result["stderr"] = ""

        return result

    # Handle other Python-side errors from the subprocess
    except JuliaSubprocessOtherError as e:
        result = {
            "error": True,
            "error_message": str(e),
            "error_stacktrace": e.traceback_str,
        }

        # Add empty output fields if capture was requested
        if capture_output:
            result["stdout"] = ""
            result["stderr"] = ""

        return result

    # Handle timeout
    except TimeoutError as e:
        result = {
            "error": True,
            "error_message": str(e),
            "error_stacktrace": None,
        }

        # Add empty output fields if capture was requested
        if capture_output:
            result["stdout"] = ""
            result["stderr"] = ""

        return result

    # Catch unexpected Python errors
    except Exception as e:
        result = {
            "error": True,
            "error_message": f"Unexpected error: {str(e)}",
            "error_stacktrace": traceback.format_exc(),
        }

        # Add empty output fields if capture was requested
        if capture_output:
            result["stdout"] = ""
            result["stderr"] = ""

        return result


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


def get_julia_output(code: str) -> str:
    """
    Execute Julia code and return only the captured output as a string.

    Args:
        code (str): The Julia code to execute.

    Returns:
        str: The combined stdout and stderr output from Julia execution.
             If there's an error, returns the error message instead.
    """
    result = run_string(code, capture_output=True)

    if result["error"]:
        return get_error_message(result)
    else:
        output_parts = []
        if result.get("stdout"):
            output_parts.append(result["stdout"])
        if result.get("stderr"):
            output_parts.append(f"STDERR: {result['stderr']}")

        return "\n".join(output_parts) if output_parts else ""


def run_string_with_output(code: str):
    """
    Convenience function that runs Julia code and always captures output.

    Args:
        code (str): The Julia code to execute.

    Returns:
        dict: Same as run_string(code, capture_output=True)
    """
    return run_string(code, capture_output=True)
