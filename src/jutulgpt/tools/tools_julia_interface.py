from jutulgpt.julia_interface import run_string
from jutulgpt.utils import logger


def run_julia_code(code: str) -> str:
    """Executes Julia code and returns output or error."""
    logger.info(f"run_julia_code tool is invoked with code {code}")
    run_state = run_string(code)

    if run_state["error"]:
        return run_state["error_message"]

    return run_state["out"]
