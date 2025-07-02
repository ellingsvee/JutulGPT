from jutulgpt.graph import graph
from jutulgpt.utils import load_lines_from_txt

if __name__ == "__main__":
    questions = load_lines_from_txt("examples/julia_questions.txt")
    # question = "Generate code for printing Hello World."
    # question = "Write some Julia code that throws an error with an error message when executed."
    question = questions[2]
    print("Question:", question)
    result = graph.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )
    print("Result:", result)
