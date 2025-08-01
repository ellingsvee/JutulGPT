from jutulgpt.cli import print_to_console
from jutulgpt.julia.get_function_documentation_from_code import (
    get_function_documentation_from_code,
    get_function_documentation_from_function_names,
)

code_str = """
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

if __name__ == "__main__":
    out = get_function_documentation_from_code(code_str)
    print(out)

    out2 = get_function_documentation_from_function_names(
        ["setup_vertical_well", "setup_well", "reservoir_domain"]
    )
    print(out2)
