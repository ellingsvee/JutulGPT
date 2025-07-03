import getpass
import logging
import os


from langchain_ollama import ChatOllama, OllamaEmbeddings


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


# _set_env("OPENAI_API_KEY")


max_iterations = 5
reflection_flag = "reflect"
model_name = "llama3-groq-tool-use:8b"
# model_name = "gemma3n:latest"

logging_level = logging.INFO

llm = ChatOllama(model=model_name)
embedding = OllamaEmbeddings(model="nomic-embed-text")
