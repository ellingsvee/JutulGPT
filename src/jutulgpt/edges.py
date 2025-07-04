from jutulgpt.config import max_iterations, reflection_flag
from jutulgpt.utils import logger


def decide_to_finish(state):
    if state["error"] == "no" or state["iterations"] == max_iterations:
        # print("---DECISION: FINISH---")
        logger.info("Decision: Finish")
        if state["iterations"] == max_iterations:
            print(f"Max iterations {max_iterations} reached.")
        return "end"
    # print("---DECISION: RETRY---")
    logger.info("Decision: Retry")
    # return "reflect" if reflection_flag == "reflect" else "generate"
    return "generate"
