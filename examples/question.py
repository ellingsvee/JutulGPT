from jutulgpt.graph import graph
from jutulgpt.utils import load_lines_from_txt

if __name__ == "__main__":
    questions = load_lines_from_txt("examples/julia_questions.txt")
    # question = questions[9]

    # question = "Can you check the JutulDarcy documentation fo how to use the CartesianMesh function?"
    question = f"""
I have the following Julia code. Can you modufy it so the size of the physical_dims is half of what it is now?

using JutulDarcy, Jutul
Darcy, bar, kg, meter, day = si_units(:darcy, :bar, :kilogram, :meter, :day)
nx = ny = 25
nz = 10
cart_dims = (nx, ny, nz)
physical_dims = (1000.0, 1000.0, 100.0).*meter
g = CartesianMesh(cart_dims, physical_dims)
domain = reservoir_domain(g, permeability = 0.3Darcy, porosity = 0.2)
Injector = setup_vertical_well(domain, 1, 1, name = :Injector)
Producer = setup_well(domain, (nx, ny, 1), name = :Producer)
"""

    for chunk in graph.stream({"messages": [("user", question)]}):
        for node, update in chunk.items():
            try:
                update["messages"][-1].pretty_print()
            except Exception as e:
                pass
