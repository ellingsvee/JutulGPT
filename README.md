# JutulGPT

Using LLMS to work with the JutulDarcy package.

## Settings and configuration
The agent is configured in the `src/jutulgpt/configuration.py` file. 

The static settings are:
- `USE_LOCAL_MODEL`: Set to `True` for using local models through Ollama.
- `MAX_ITERATIONS`: If the generated code fails. How many times the model will try to fix the code.
- `HUMAN_INTERACTION`: Set to `True` for enabling human-in-the-loop. This only works in the UI.
- `RETRIEVE_FIMBUL`: Whether to retrieve Fimbul documentation or not. If False, it will only retrieve JutulDarcy documentation.
- `ALLOW_PACKAGE_INSTALLATION`: Set to `True` to allow the agent to install packages. If `False` the `check_code` step will fail if it finds any installation in the generated code.
- `N_RETRIEVED_DOCS`:  Number of documents to retrieve in RAG.
- `N_RETRIEVED_EXAMPLES`:  Number of examples to retrieve in RAG.

In addition to the static settings we also sett chat- and embedding models, rerankers, and RAG search types in the `BaseConfiguration` and `AgentConfiguration`. Note that all static settings should eventually be integrated into this configuration to allow the most flexible setup. You specify the following settings:
- `embedding_model`: Name of the embedding model to use.
- `retriever_provider`: The vector store provider to use for retrieval.
- `search_type`: Defines the type of search that the retriever should perform.
- `search_kwargs`: Additional keyword arguments to pass to the search function of the retriever. See Langgraph documentation for details about what kwargs works for the different search types. Note that the `k`keyword is set in the retriever specs by the `N_RETRIEVED_DOCS` and `N_RETRIEVED_EXAMPLES` variables.
- `rerank_provider`: The provider user for reranking the retrieved documents.
- `rerank_kwargs`: Keyword arguments provided to the reranker.
- `response_model`: The language model used for generating responses. Should be in the form: provider/model-name. Currently I have only tested using `OpenAI` or `Ollama` models, but should be easy to extend to other providers.
- `default_coder_prompt`: The default prompt used for generating Julia code.


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

## Known issues
- In the `check_code` function, the generated code is modified for reducing runtime and avoiding softlocks. However, the current code is not perfect, and should be improved.
- Strange to separate the static settings from the runnable config. All should eventually be included in the runnable configuration.

## Potential improvements
- Update UI using a callback when running the Julia code. As of now there is no clear indication that the program is running.
- If the agent tries to invoke a RAG tool, we can currently only modify the query. It would be nice to be able to reject the use of RAG.
- Would be nice if we could modify the runnable configuration from the UI. F.ex. change what model we use, or the number of documents to retrieve during RAG.
- Extend to a better CLI based workflow. The current setup primarily meant to be run throught the UI.
- A more flexible RAG setup.
- Extend the workflow to a sub-agent collaboration.F.ex. as described here: [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)