from typing import Annotated

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg
from pydantic import BaseModel, Field

# from jutulgpt import configuration
import jutulgpt.rag.retrieval as retrieval
import jutulgpt.rag.split_docs as split_docs
import jutulgpt.rag.split_examples as split_examples
from jutulgpt.configuration import BaseConfiguration
from jutulgpt.human_in_the_loop import modify_rag_query, response_on_rag
from jutulgpt.rag.retriever_specs import RETRIEVER_SPECS
from jutulgpt.utils import get_file_source


class ReadFromFileInput(BaseModel):
    file_path: str = Field(
        "The absolute path to the file to read from",
    )


class ReadFromFile(BaseTool):
    name: str = "read_from_file"
    description: str = "Read from a file and return its content as a string."
    args_schema = ReadFromFileInput

    def _run(
        self, file_path: str, config: Annotated[RunnableConfig, InjectedToolArg]
    ) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except PermissionError:
            return f"Error: Permission denied when accessing: {file_path}"
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"


class WriteToFileInput(BaseModel):
    file_path: str = Field(
        "The absolute path to the file to write to",
    )
    content: str = Field(
        "The content to write to the file",
    )


class WriteToFile(BaseTool):
    name: str = "write_to_file"
    description: str = (
        "Write a string to a file. If the file exists, it will be overwritten."
    )
    args_schema = WriteToFileInput

    def _run(
        self,
        file_path: str,
        content: str,
        config: Annotated[RunnableConfig, InjectedToolArg],
    ) -> str:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                return f"Successfully wrote to file: {file_path}"
        except Exception as e:
            return f"Error writing to file {file_path}: {str(e)}"
