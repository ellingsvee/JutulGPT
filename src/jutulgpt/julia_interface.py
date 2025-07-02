from juliacall import JuliaError
from juliacall import Main as jl


def run_string(code: str):
    try:
        return {"out": jl.seval(code), "error": False, "error_message": None}
    except JuliaError as e:
        return {"out": None, "error": True, "error_message": str(e)}
