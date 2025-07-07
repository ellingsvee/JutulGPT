from langchain_core.messages import convert_to_messages
from jutulgpt.graph import graph
from jutulgpt.state import Code
from jutulgpt.utils import format_code_response, load_lines_from_txt
from jutulgpt.state import GraphState

if __name__ == "__main__":
    questions = load_lines_from_txt("examples/julia_questions.txt")
    question = questions[9]

    # question = "Can you check the JutulDarcy documentation for it says about the CartesianMesh function?"

    # print("Question:", question)
    # result = graph.invoke(
    #     {"messages": [("user", question)], "code": "", "iterations": 0, "error": ""}
    # )

    # result["messages"][-2].pretty_print()
    # result["messages"][-1].pretty_print()
    # print(result)

    init_state = GraphState(
        messages=convert_to_messages([{"role": "user", "content": question}]),
        structured_response=Code(prefix="", imports="", code=""),
        iterations=0,
        error=False,
    )

    for chunk in graph.stream(
        # {"messages": [("user", question)], "code": "", "iterations": 0, "error": ""}
        init_state
    ):
        for node, update in chunk.items():
            # print("Update from node", node)
            # update["messages"][-2].pretty_print()
            update["messages"][-1].pretty_print()
