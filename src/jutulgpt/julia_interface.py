from juliacall import JuliaError
from juliacall import Main as jl


def run_string(code: str):
    try:
        return {"out": jl.seval(code), "error": False, "error_message": None}
    except JuliaError as e:
        # return {"out": None, "error": True, "error_message": str(e)}
        full_msg = str(e)
        if "\nStacktrace:\n" in full_msg:
            pre_stack, stack = full_msg.split("\nStacktrace:\n", 1)
            pre_stack = pre_stack.strip()
            stack = stack.strip()
        else:
            pre_stack = full_msg.strip()
            stack = None

        return {
            "out": None,
            "error": True,
            "error_message": pre_stack,
            "error_stacktrace": stack,
        }
