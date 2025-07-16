import re
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Union

from juliacall import JuliaError
from juliacall import Main as jl

from jutulgpt.configuration import static_config
from jutulgpt.state import CodeBlock, State
from jutulgpt.utils import split_code_into_lines

# TODO: To handle the impoort of GLMakie. This works when run from terminal, but not in the iteractive environment.
# See: https://juliapy.github.io/PythonCall.jl/stable/compat/#Asynchronous-Julia-code-(including-Makie)
jl_yield = getattr(jl, "yield")

# jl.seval("using JutulDarcy, Jutul")  # Ensure JutulDarcy is loaded


def run_string(code: str):
    """Execute Julia code from a string and capture output or detailed errors."""
    try:
        result = jl.seval(code)
        while True:
            jl_yield()
            state = wait(result, timeout=0.1)
            if not state.not_done:
                break

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


def run_string_line_by_line(code: str):
    """Execute Julia code line by line and capture output or errors. An error is returned for the first line that failed."""
    # lines = code.splitlines()
    out = None
    if code.strip() != "":
        lines = split_code_into_lines(code)

        print("Running code line by line:")
        for line in lines:
            print(f"- Running line: {line.strip()}")

            if not line.strip():
                continue  # Skip empty lines

            try:
                import_statement = line.strip().startswith("using")
                if import_statement:  # To handle the import of GLMakie.
                    # jl_yield()
                    result = jl.seval(line)
                    jl_yield()
                else:
                    result = jl.seval(line)
                    jl_yield()

                out = result
            except JuliaError as e:
                full_msg = str(e).strip()
                pre_stack, stack = _split_stacktrace(full_msg)
                filtered_stack = _filter_stacktrace(stack) if stack else None
                return {
                    "out": None,
                    "error": True,
                    "error_message": pre_stack,
                    "error_stacktrace": filtered_stack,
                    "line": line.strip(),
                }

        print("Finished running code line by line")

    return {
        "out": out,
        "error": False,
        "error_message": None,
        "error_stacktrace": None,
        "line": None,
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
    out_string = f"{result['error_message']}"
    if result["error_stacktrace"] is not None:
        out_string += f"\n\nStacktrace:\n{result['error_stacktrace']}"
    return out_string


def _get_code_string_from_response(response: str) -> str:
    """Extract code from a Markdown-style Julia code block in the response string."""
    match = re.search(r"```julia\s*([\s\S]*?)```", response, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def get_code_from_response(response: str) -> CodeBlock:
    """Extracts Julia code and imports from a Markdown code block and returns a CodeBlock object."""
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
    last_message = state.messages[-1]
    if last_message.type == "ai":
        last_message_content = last_message.content
    else:
        last_message_content = ""
    code_block = get_code_from_response(last_message_content)
    return code_block
