from jutulgpt.julia.get_linting_result import get_linting_result

code_str = """
using JutulDarcy, Jutul
Darcy, bar, kg, meter, day = si_unitsWRONG(:darcy, :bar, :kilogram, :meter, :day)
nx = ny = 25
nz = 10
cart_dims = (nx, ny, nz)
physical_dims = (1000.0, 1000.0, 100.0).*meter
g = CartesianMeshWRONG(cart_dims, physical_dims)
domain = reservoir_domain(g, permeability = 0.3Darcy, porosity = 0.2)
Injector = setup_vertical_well(domain, 1, 1, name = :Injector)
Producer = setup_well(domain, (nx, ny, 1), name = :Producer)
"""

if __name__ == "__main__":
    print("=== Testing linting result extraction ===")
    out = get_linting_result(code_str)
    print("Output: " + out)
