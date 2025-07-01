from IPython.display import Image, display


def plot_graph(graph):
    """
    Display a graph using the Mermaid format.

    Args:
        graph: A compiled StateGraph object.
    """
    try:
        display(Image(graph.get_graph().draw_mermaid_png()))
    except Exception:
        # This requires some extra dependencies and is optional
        pass
