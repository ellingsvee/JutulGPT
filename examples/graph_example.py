from jutulgpt.graph import app
from jutulgpt.utils import plot_graph, save_graph_ascii

if __name__ == "__main__":
    # Example question
    question = "Generate Julia code for setting up a simple reservoir simulation"

    print("=== JutulGPT Graph Visualization Example ===")
    print(f"Question: {question}")
    print("-" * 50)

    # Plot the graph structure (will save to file and open in browser)
    print("Plotting graph structure...")
    plot_graph(app, save_path="jutulgpt_graph.png")

    # Alternative: save as text representation
    print("\nSaving graph structure as text...")
    save_graph_ascii(app, "jutulgpt_graph_structure.txt")

    # Run the actual question
    print("\nRunning the question through the graph...")
    result = app.invoke(
        {"messages": [("user", question)], "iterations": 0, "error": ""}
    )

    print("\nResult:")
    print(result)
