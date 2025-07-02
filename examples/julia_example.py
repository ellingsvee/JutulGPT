from jutulgpt.graph import graph
from jutulgpt.utils import format_code_response, load_lines_from_txt

if __name__ == "__main__":
    questions = load_lines_from_txt("examples/julia_questions.txt")
    question = questions[4]

    # question = "What is the 2 times 3. You dont need to write any Julia code, just determine the answer using your available tools. Return as a single number in the predix of the response."

    print("Question:", question)
    result = graph.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )
    print(format_code_response(result["code"]))
