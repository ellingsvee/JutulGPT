from jutulgpt.graph import graph

if __name__ == "__main__":
    question = "Generate Julia code for printing Hello World."
    # question = "Write some Julia code that throws an error with an error message when executed."
    result = graph.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )
    print("Result:", result)
