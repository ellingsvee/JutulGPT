import os
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from pydantic import BaseModel, Field
from rich.panel import Panel

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import BaseConfiguration, cli_mode
from jutulgpt.globals import console


class ReadFromFileInput(BaseModel):
    file_path: str = Field(
        "The absolute path to the file to read from",
    )


@tool("read_from_file", args_schema=ReadFromFileInput)
def read_from_file_tool(
    file_path: str, config: Annotated[RunnableConfig, InjectedToolArg]
) -> str:
    """Read from a file and return its content as a string."""
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


@tool("write_to_file", args_schema=WriteToFileInput)
def write_to_file_tool(
    file_path: str,
    content: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Write a string to a file. If the file exists, it will prompt for confirmation before overwriting."""
    configuration = BaseConfiguration.from_runnable_config(config)

    # Check if file already exists
    if os.path.exists(file_path):
        try:
            # Read existing content for preview
            with open(file_path, "r", encoding="utf-8") as f:
                existing_content = f.read()

            if cli_mode:
                # Create preview of existing content (first 300 chars)
                existing_preview = existing_content[:300]
                if len(existing_content) > 300:
                    existing_preview += "..."

                # Create preview of new content (first 300 chars)
                new_preview = content[:300]
                if len(content) > 300:
                    new_preview += "..."

                # Display confirmation prompt with previews
                console.print(
                    Panel.fit(
                        f"[bold yellow]File Already Exists: {file_path}[/bold yellow]\n\n"
                        f"[bold]Current content ({len(existing_content)} chars):[/bold]\n"
                        f"[dim]{existing_preview}[/dim]\n\n"
                        f"[bold]New content ({len(content)} chars):[/bold]\n"
                        f"[dim]{new_preview}[/dim]",
                        title="File Overwrite Confirmation",
                        border_style="yellow",
                    )
                )

                # Prompt for confirmation
                response = (
                    console.input(
                        "\n[bold red]Do you want to overwrite this file? (y/n): [/bold red]"
                    )
                    .strip()
                    .lower()
                )

                if response not in ["y", "yes"]:
                    print_to_console(
                        text=f"File write cancelled by user: {file_path}",
                        title="File Writer",
                        border_style=colorscheme.warning,
                    )
                    return f"File write cancelled by user: {file_path}"
            else:  # UI mode
                from jutulgpt.human_in_the_loop.ui import response_on_file_write

                write_to_file, file_path = response_on_file_write(file_path)
                if not write_to_file:
                    return f"File write cancelled by user: {file_path}"

        except Exception as e:
            print_to_console(
                text=f"Error reading existing file {file_path}: {str(e)}",
                title="File Writer Warning",
                border_style=colorscheme.warning,
            )
            # Continue with write attempt even if we can't read existing file

    # Show what we're writing (truncated preview)
    print_content = content[:500] + "..." if len(content) > 500 else content
    print_to_console(
        text=f"Writing to {file_path}",
        title="File Writer",
        border_style=colorscheme.warning,
    )

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            success_msg = (
                f"Successfully wrote {len(content)} characters to file: {file_path}"
            )
            print_to_console(
                text=success_msg,
                title="File Writer Success",
                border_style=colorscheme.success,
            )
            return success_msg
    except Exception as e:
        error_msg = f"Error writing to file {file_path}: {str(e)}"
        print_to_console(
            text=error_msg,
            title="File Writer Error",
            border_style=colorscheme.error,
        )
        return error_msg
