# JutulGPT

An AI assistant for JutulDarcy!

![CLI example](media/JutulGPT_CLI.png "CLI example")

## Getting started

### Prerequisites

This project requires both **Python** and **Julia**, along with some system-level dependencies. Make sure these are installed:
- `git`: See [git downloads](https://git-scm.com/downloads).
- `Python3 >=3.12`: See NOTE or [Download Python](https://www.python.org/downloads/)
- `Julia`: Package tested on version 1.11.6. See [Installing Julia](https://julialang.org/install/).
- `build-essential`
- `graphviz` and `graphviz-dev`: See [Graphviz download](https://graphviz.org/download/)

Optional:
- `uv`: Recommended package manager. See [Installing uv](https://docs.astral.sh/uv/getting-started/installation/).
- `ollama`: For running local models. See [Download Ollama](https://ollama.com/download).

> NOTE: See [Installing python](https://docs.astral.sh/uv/guides/install-python/) for installing Python using `uv`. 



### Step 1: Python
Retireve the code by cloning the repository
```bash
# Clone and choose the repo
git clone https://github.com/ellingsvee/JutulGPT.git
cd JutulGPT/
```
If you are using `uv`, initialize the environment by
```bash
# Initialize the enviroment
uv venv
source .venv/bin/activate

# Install packages
uv sync
```

If encountering an error due to the `pygraphviz` package, try explicitly installing it using
```bash
brew install graphviz
uv add --config-settings="--global-option=build_ext" \
            --config-settings="--global-option=-I$(brew --prefix graphviz)/include/" \
            --config-settings="--global-option=-L$(brew --prefix graphviz)/lib/" \
            pygraphviz
```

Alternatively, if you use `pip`, create and activate the virtual environment by
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .  # or `pip install -e .[dev]` for development
```
### Step 2: Julia
For running Julia code we also need to set up a working Julia project. 
```bash
julia
# In Julia
julia> import Pkg; Pkg.activate("."); Pkg.instantiate()
```
This will install all the necessary packages listed in the `Project.toml` the first time you invoke the agent.


### Step 3: Setup environment
You then have to set the environment variables. Generate a `.env` file by
```bash
cp .env.example .env
```
and modify it by providing your own `OPENAI_API_KEY` key.  For running in the UI you also must provide an `LANGSMITH_API_KEY` key.


### Step 4: Test it!

Finally, try to initialize the agent by
```bash
uv run examples/agent.py
```
This should install the necessary Julia packages before running. You might need to re-run the model after the installation.


## Basic usage
Two different agents are implemented.

### `Agent`
The first agent follows an evaluator-optimizer workflow, where code is first generated and then evaluated. This strategy works well for smaller models and more specific tasks. It is f.ex. suggested to use this model for generating code to set up a simulation.

![Evaluator Optimizer](media/Evaluator_optimizer.png "Evaluator Optimizer")

Run the agent in the CLI by
```bash
uv run examples/agent.py
```

### `Autonomous Agent`
The second agent has more available tools, and can interact with the environment in a more sophisticated way. For sufficiently large LLMs, this agent can provide a more _Copilot_-like experience.

![Autonomous Agent](media/Autonomous_Agent.png "Autonomous Agent")

Run the agent in the CLI by
```bash
uv run examples/autonomous_agent.py
```

## Settings and configuration
The agent is configured in the `src/jutulgpt/configuration.py` file.  

The two main settings you must specify are
```bash
# Static settings
cli_mode: bool = True

# Select whether to use local models through Ollama or use OpenAI
LOCAL_MODELS = False
LLM_MODEL_NAME = "ollama:qwen3:14b" if LOCAL_MODELS else "openai:gpt-4.1"
EMBEDDING_MODEL_NAME = (
    "ollama:nomic-embed-text" if LOCAL_MODELS else "openai:text-embedding-3-small"
)
```

More advanced settings are set in the `BaseConfiguration`. LangGraph will turn these into a `RunnableConfig`, which enables easier configuration at runtime.  You specify the following settings:
- `human_interaction`: Enable human-in-the-loop. See the `HumanInteraction` class in the configuration file for detailed control.
- `embedding_model`: Name of the embedding model to use. By default equal to the `EMBEDDING_MODEL_NAME`.
- `retriever_provider`: The vector store provider to use for retrieval.
- `examples_search_type`: Defines the type of search that the retriever should perform when retrieving examples.
- `examples_search_kwargs`: Keyword arguments to pass to the search function of the retriever when retrieving examples. See [LangGraph documentation](https://python.langchain.com/api_reference/chroma/vectorstores/langchain_chroma.vectorstores.Chroma.html#langchain_chroma.vectorstores.Chroma.as_retriever) for details about what arguments works for the different search types.
- `rerank_provider`: The provider user for reranking the retrieved documents.
- `rerank_kwargs`: Keyword arguments provided to the reranker.
- `agent_model`: The language model used for generating responses. Should be in the form: provider/model-name. Currently I have only tested using `OpenAI` or `Ollama` models, but should be easy to extend to other providers. By default equal to the `LLM_MODEL_NAME`.
- `autonomous_agent_model`: See `agent_model`.
- `agent_prompt`: The prompt used for the agent.
- `autonomous_agent_prompt`: The prompt used for the autonomous agent.

The settings can be specified by passing a configuration dictionary when invoking the models. See f.ex the `run()` function in `src/jutulgpt/agents/agent_base.py`. Alternatively, the GUI provides a custom interface where the settings can be selected.

## Interfaces
### CLI 

Enable the CLI-mode by in `src/jutulgpt/configuration.py` setting
```python
cli_mode = True
```
This gives you a nice interface for asking questions, retrieving info, generating and running code etc. Both agents can also read and write to files.

### GUI
![GUI example](media/JutulGPT_GUI.png "GUI example")

The JutulGPT also has an associated GUI called [JutulGPT-GUI](https://github.com/ellingsvee/JutulGPT-GUI).  For using the GUI, you must disable the CLI-mode. To this by setting `cli_mode = False` in `src/jutulgpt/configuration.py`.

Install it by following the instructions in the repository. Alternatively do
```bash
cd .. # Move to parent directory
git clone https://github.com/ellingsvee/JutulGPT-GUI.git # Clone JutulGPT-GUI
cd JutulGPT-GUI/
pnpm install
cd ../JutulGPT/ # Move back to JutulGPT
```

To run the GUI locally, you have to use the [LangGraph CLI](https://langchain-ai.github.io/langgraph/cloud/reference/cli/) tool. Start it by
```bash
langgraph dev # Run from JutulGPT/ directory
```
and start the GUI from the JutulGPT-GUI directory by running
```bash
pnpm dev # Run from JutulGPT-GUI/ directory
```
The GUI can now be accessed on `http://localhost:3000/` (or some other location depending on your JutulGPT-GUI configuration).

> NOTE: Remember to set `cli_mode = False` in `src/jutulgpt/configuration.py`.

## Fimbul (WARNING)
There is some legacy code for generating code for the Fimbul package. I have removed a lot of it, but it can be re-implemented by adding some tools and modifying the prompts. My suggestion is to get familiar with the current tools fot JutulDarcy, and then later extend to Fimbul.

## Testing (WARNING)
Tests are set up to be implemented using [pytest](https://docs.pytest.org/en/stable/). They can be written in the `tests/` directory. Run by the command
```bash
uv run pytest
```
> Note: Due to a lot of rapid modifications the previous tests were remove doe to being outdated. Work is being done to update this!

