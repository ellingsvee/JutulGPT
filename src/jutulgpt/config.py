import getpass
import logging
import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


load_dotenv()
_set_env("OPENAI_API_KEY")


max_iterations = 2
# model_name = "llama3-groq-tool-use:8b"
model_name = "qwen2.5-coder:14b"
# model_name = "qwen2.5:32b"
# model_name = "gemma3n:latest"
# model_name = "mistral:7b-instruct-v0.3-q8_0"
# model_name = "deepseek-r1:8b"

logging_level = logging.INFO

llm = ChatOllama(model=model_name)
embedding = OllamaEmbeddings(model="nomic-embed-text")

# llm = init_chat_model("openai:gpt-4.1", temperature=0)
# llm = init_chat_model("openai:gpt-4.1-mini", temperature=0)
# embedding = OpenAIEmbeddings()

avoid_tools = False
