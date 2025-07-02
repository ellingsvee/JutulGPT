from jutulgpt.graph import graph

if __name__ == "__main__":
    # question = "Generate Julia code for printing Hello World."
    question = "Write some Julia code that will intentionally fail to run."
    result = graph.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )
