from jutulgpt import graph
from jutulgpt.utils import load_lines_from_txt

if __name__ == "__main__":
    questions = load_lines_from_txt("examples/jutuldarcy_questions.txt")
    question = questions[0]

    for chunk in graph.stream({"messages": [("user", question)]}):
        for node, update in chunk.items():
            try:
                update["messages"][-1].pretty_print()
            except Exception:
                pass
