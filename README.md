# JutulGPT

Using LLMS to work with the JutulDarcy package.

## Installation
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
You then have to set the environment variables. Generate a `.env` file by
```bash
cp .env.example .env
```
and modify it by providing your own `OPENAI_API_KEY`and `LANGSMITH_API_KEY` keys.

For enabling generative UI components do 
```bash
cd src/ui
pnpm install
cd ../..
```
Finally, try to run some code by
```bash
uv run examples/question.py
```
This should install the necessary Julia packages before running.

## Fimbul
For using the model to generate code for [Fimbul](https://github.com/sintefmath/Fimbul.jl), install the package by cloning the repository
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


## UI
The JutulGPT has an associated UI called [JutulGPT-UI](https://github.com/ellingsvee/JutulGPT-UI). Install it by following the instructions in the repository. Alternatively do
```bash
cd .. # Move to parent directory
git clone https://github.com/ellingsvee/JutulGPT-UI.git # Clone JutulGPT-UI
cd JutulGPT-UI/
pnpm install
cd ../JutulGPT/ # Move back to JutulGPT
```

To run the UI locally, you have to use the [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/) tool. Start it by
```bash
langgraph dev # Run from JutulGPT/ directory
```
and start the UI from the JutulGPT-UI directory by running
```bash
pnpm dev # Run from JutulGPT-UI/ directory
```
The UI can now be accessed on `http://localhost:3000/` (or some other location depending on your JutulGPT-UI configuration).


Note, if you plan on using the UI, you must also set `interactive_environment = True` in `src/jutulgpt/configuration.py`. If not, any human in the loop interaction is disabled.

## Testing
Tests are implemented using [pytest](https://docs.pytest.org/en/stable/). Run tests by
```bash
uv run pytest
```