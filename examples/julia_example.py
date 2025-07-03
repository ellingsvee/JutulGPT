from jutulgpt.graph import graph
from jutulgpt.utils import format_code_response, load_lines_from_txt

if __name__ == "__main__":
    questions = load_lines_from_txt("examples/julia_questions.txt")
    question = questions[5]

    question = "Can you check the JutulDarcy documentation for what different types of wells we can simulate? You dont need to write any code."

    print("Question:", question)
    result = graph.invoke(
        {"messages": [("user", question)], "code": "", "iterations": 0, "error": ""}
    )
    print(format_code_response(result["code"]))
