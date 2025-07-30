from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool, InjectedToolArg
from pydantic import BaseModel, Field

# from jutulgpt import configuration
from jutulgpt.cli import colorscheme, print_to_console


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
        print_to_console(
            text=f"Reading from {file_path}",
            title="File Reader",
            border_style=colorscheme.warning,
        )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        except FileNotFoundError:
            print_to_console(
                text=f"File not found: {file_path}",
                title="File Reader Error",
                border_style=colorscheme.error,
            )
            return f"Error: File not found: {file_path}"
        except PermissionError:
            print_to_console(
                text=f"Permission denied when accessing: {file_path}",
                title="File Reader Error",
                border_style=colorscheme.error,
            )
            return f"Error: Permission denied when accessing: {file_path}"
        except Exception as e:
            print_to_console(
                text=f"Error reading file {file_path}: {str(e)}",
                title="File Reader Error",
                border_style=colorscheme.error,
            )
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
        print_to_console(
            text=f"Writing to {file_path}",
            title="File Writer",
            border_style=colorscheme.warning,
        )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
                return f"Successfully wrote to file: {file_path}"
        except Exception as e:
            print_to_console(
                text=f"Error writing to file {file_path}: {str(e)}",
                title="File Writer Error",
                border_style=colorscheme.error,
            )
            return f"Error writing to file {file_path}: {str(e)}"
