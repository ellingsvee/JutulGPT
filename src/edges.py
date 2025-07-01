from config import max_iterations, reflection_flag


def decide_to_finish(state):
    if state["error"] == "no" or state["iterations"] == max_iterations:
        print("---DECISION: FINISH---")
        return "end"
    print("---DECISION: RETRY---")
    return "reflect" if reflection_flag == "reflect" else "generate"
