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


def _run_julia_code(code_string, return_queue):
    """
    Helper function to execute Julia code in a subprocess and return the result or error via a queue.

    Args:
        code_string (str): The Julia code to execute.
        return_queue (multiprocessing.Queue): Queue to put the result or error information.
    """
    try:
        from juliacall import Main as jl_sub

        jl_sub.seval(code_string)
        # result = jl_sub.seval(code_string)
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


def jl_eval_in_subprocess(code_string, timeout=30):
    """
    Execute Julia code in a separate subprocess for isolation and error handling.

    Args:
        code_string (str): The Julia code to execute.
        timeout (int, optional): Maximum time in seconds to allow for execution.

    Returns:
        The result of the Julia code execution if successful.

    Raises:
        JuliaSubprocessJuliaError: If a JuliaError occurs in the subprocess.
        JuliaSubprocessOtherError: If a non-Julia error occurs in the subprocess.
        TimeoutError: If the execution exceeds the timeout.
    """
    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    p = ctx.Process(target=_run_julia_code, args=(code_string, q))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        raise TimeoutError("Julia code timed out.")

    success, result = q.get()
    if success:
        return result
    else:
        if result["type"] == "JuliaError":
            raise JuliaSubprocessJuliaError(
                result["message"], result.get("jl_stacktrace")
            )
        else:
            raise JuliaSubprocessOtherError(result["message"], result["traceback"])


def run_string(code: str):
    """
    Execute a Julia code string in a subprocess and return the result or error details.

    Args:
        code (str): The Julia code to execute.

    Returns:
        dict: A dictionary with keys 'out', 'error', 'error_message', and 'error_stacktrace'.
    """
    try:
        jl_eval_in_subprocess(code)
        return {
            "error": False,
            "error_message": None,
            "error_stacktrace": None,
        }

    # Handle Julia errors raised from within the subprocess
    except JuliaSubprocessJuliaError as e:
        print("Inside JuliaSubprocessJuliaError in run_string")
        filtered_stack = (
            _filter_stacktrace(e.traceback_str) if e.traceback_str else None
        )
        print(f"filtered_stack: {filtered_stack}")
        return {
            "error": True,
            "error_message": str(e),
            "error_stacktrace": filtered_stack,
        }

    # Handle other Python-side errors from the subprocess
    except JuliaSubprocessOtherError as e:
        return {
            "error": True,
            "error_message": str(e),
            "error_stacktrace": e.traceback_str,
        }

    # Handle timeout
    except TimeoutError as e:
        return {
            "error": True,
            "error_message": str(e),
            "error_stacktrace": None,
        }

    # Catch unexpected Python errors
    except Exception as e:
        return {
            "error": True,
            "error_message": f"Unexpected error: {str(e)}",
            "error_stacktrace": traceback.format_exc(),
        }


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
