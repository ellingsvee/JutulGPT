import re
from typing import Union

from juliacall import JuliaError
from juliacall import Main as jl

from jutulgpt.state import Code

jl.seval("using JutulDarcy, Jutul")  # Make sure these packages are always imported


def run_string(code: str):
    """Execute Julia code from a string and capture output or detailed errors."""
    try:
        result = jl.seval(code)
        return {
            "out": result,
            "error": False,
            "error_message": None,
            "error_stacktrace": None,
        }
    except JuliaError as e:
        full_msg = str(e).strip()
        pre_stack, stack = _split_stacktrace(full_msg)
        filtered_stack = _filter_stacktrace(stack) if stack else None
        return {
            "out": None,
            "error": True,
            "error_message": pre_stack,
            "error_stacktrace": filtered_stack,
        }


def _split_stacktrace(msg: str):
    """Helper to split Julia error messages into message and stacktrace parts."""
    marker = "\nStacktrace:\n"
    if marker in msg:
        pre_stack, stack = msg.split(marker, 1)
        return pre_stack.strip(), stack.strip()
    return msg, None


def _filter_stacktrace(stack: str) -> Union[str, None]:
    """Filter out Julia stacktrace lines related to PythonCall and juliacall internals."""
    lines = stack.splitlines()
    keep_lines = []
    for line in lines:
        # Keep if it's not in PythonCall or JlWrap packages
        if not re.search(r"PythonCall|JlWrap|juliacall|pyjlmodule_seval", line):
            keep_lines.append(line)
    return "\n".join(keep_lines) if keep_lines else None


def get_error_message(result) -> str:
    out_string = f"Julia error message: {result['error_message']}\n"
    if result["error_stacktrace"] is not None:
        out_string += f"Julia stacktrace: {result['error_stacktrace']}"
    return out_string


def _get_code_string_from_response(response: str) -> str:
    """Extract code from a Markdown-style Julia code block in the response string."""
    match = re.search(r"```julia\s*([\s\S]*?)```", response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def get_code_from_response(response: str) -> Code:
    """Extracts Julia code and imports from a Markdown code block and returns a Code object."""
    code_str = _get_code_string_from_response(response)
    if not code_str:
        return Code(imports="", code="")

    import_lines = []
    code_lines = []
    for line in code_str.splitlines():
        if line.strip().startswith(("using ")):
            import_lines.append(line.strip())
        else:
            code_lines.append(line)

    return Code(imports="\n".join(import_lines), code="\n".join(code_lines).strip())
