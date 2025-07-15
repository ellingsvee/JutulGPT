# JutulGPT

Using LLMS to work with the JutulDarcy package.

## Installation
### Initialization
It is recommended to install and run JutulGPT using `uv`. See the [uv documentation](https://github.com/astral-sh/uv). Once installed, create and initialize the project by
```bash
# Clone and choose the repo
git clone https://github.com/ellingsvee/JutulGPT.git
cd JutulGPT/

# Initialize the enviroment
uv venv
source .venv/bin/activate

# Install packages
uv sync
```
### Julia and JutulDarcy
For evaluating the generated code, JutulGPT requires [Julia](https://julialang.org/) to be installed. Additionally, we need to initialize a working Julia project with [JutulDarcy](https://sintefmath.github.io/JutulDarcy.jl/dev/) installed. In your cloned repository install the package by
```bash
julia --project=.
```
```julia
using Pkg; Pkg.activate(".");
Pkg.add("JutulDarcy");
```
Furthermore, [Getting Started](https://sintefmath.github.io/JutulDarcy.jl/dev/man/intro) also recommends installing
```julia
Pkg.add("Jutul");
Pkg.add("GLMakie"); # 3D and interactive visualization
Pkg.add("Optim") # Optimization library
Pkg.add("HYPRE") # Better linear solver
Pkg.add("GeoEnergyIO") # Parsing input files
```
Additionally, for using the model to generate code for [Fimbul](https://github.com/sintefmath/Fimbul.jl), install the package by cloning the repository
```bash
cd .. # Move to parent directory
git clone https://github.com/sintefmath/Fimbul.jl.git # Clone Fimbul
cd JutulGPT/ # Move back into JutulGPT
```
```julia
using Pkg; Pkg.activate(".");
Pkg.develop(path="../Fimbul.jl/");
Pkg.instantiate()
```
For the RAG to retrieve from the Fimbul documentation, set the `retrieve_fimbul = True` in `src/jutulgpt/configuration.py`.


### LLMs

You can enter choose to run local models through [Ollama](https://ollama.com/), or use the [OpenAI API](https://openai.com/api/). Specify your models in the `src/jutulgpt/configuration.py` file. You must set the `use_openai` bool, and specify the preferred model name in the `default_model_name` and embedding model name in `embedding_model_name`.

If you use OpenAI models, you must provide an API key in the `.env` file
```
OPENAI_API_KEY=sk-proj-...
```

### UI
The JutulGPT has an associated UI called [JutulGPT-UI](https://github.com/ellingsvee/JutulGPT-UI). Install it by following the instructions in the repository. For interation between the model and the UI, generate a LangSmith API key and in `.env` set
```
LANGSMITH_API_KEY=lsv2_...
```
If you plan on using the UI, you must also set `interactive_environment = True` in `src/jutulgpt/configuration.py`.

## Running code and tests
See the `examples/` folder for some examples of how to use the agent from the terminal. Run the code by
```bash
uv run examples/chatbot.py
```
Tests are implemented using [pytest](https://docs.pytest.org/en/stable/). Run tests by
```bash
uv run pytest
```