from jutulgpt.graph import graph
from jutulgpt.utils import load_lines_from_txt

if __name__ == "__main__":
    questions = load_lines_from_txt("examples/julia_questions.txt")
    question = questions[0]
    print("Question:", question)
    result = graph.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )
    print("Result:", result["code"].code)
