from __future__ import annotations

import os
import subprocess
from typing import Optional

from langchain_core.tools import BaseTool, tool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.configuration import PROJECT_ROOT
from jutulgpt.nodes.check_code import _run_julia_code, _run_linter
from jutulgpt.utils import fix_imports, shorter_simulations


class GrepSearchInput(BaseModel):
    """Input for grep search tool."""

    query: str = Field(
        description="The keyword based pattern to search for in files. Can be a regex or plain text pattern"
    )
    includePattern: Optional[str] = Field(
        default=None, description="Search files matching this glob pattern."
    )
    isRegexp: Optional[bool] = Field(
        default=False, description="Whether the pattern is a regex."
    )


class GrepSearchTool(BaseTool):
    """Do a text search in the workspace."""

    name: str = "grep_search"
    # description: str = "Do a keyword based search in the JutulDarcy documentation. Limited to 10 results."
    description: str = "### Instructions:\nThis is best for finding exact text matches or regex patterns.\nThis is preferred over semantic search when we know the exact symbol/function name/etc. to search for.\n\nUse this tool to run fast, exact regex searches over text files.\nTo avoid overwhelming output, the results are capped at 10 matches. 2 lines of context above and below each match are included."
    args_schema: Optional[ArgsSchema] = GrepSearchInput

    def _run(
        self,
        query: str,
        includePattern: Optional[str] = None,
        isRegexp: Optional[bool] = False,
    ) -> str:
        """Search for text in files, returning each match with configurable context lines above and below."""

        context_lines = 2  # Change this to 2, 3, etc. for more context

        try:
            workspace_path = str(PROJECT_ROOT / "rag" / "jutuldarcy")
            cmd_parts = ["grep", "-r", "-n"]

            if isRegexp:
                cmd_parts.append("-E")
            else:
                cmd_parts.append("-F")  # Fixed string search

            if includePattern:
                cmd_parts.extend(["--include", includePattern])
            else:
                cmd_parts.extend(
                    [
                        "--include=*.jl",
                        "--include=*.md",
                    ]
                )

            cmd_parts.extend([query, workspace_path])

            result = subprocess.run(
                cmd_parts, capture_output=True, text=True, timeout=10
            )

            if result.stdout:
                lines = result.stdout.strip().split("\n")[:10]  # Limit to 10 results
                context_results = []
                for match in lines:
                    # Parse: filename:line_number:content
                    parts = match.split(":", 2)
                    if len(parts) != 3:
                        context_results.append(match)
                        continue
                    filename, line_str, content = parts
                    try:
                        line_num = (
                            int(line_str) - 1
                        )  # grep is 1-based, Python is 0-based
                        with open(filename, "r", encoding="utf-8") as f:
                            file_lines = f.readlines()
                        start = max(0, line_num - context_lines)
                        end = min(len(file_lines), line_num + context_lines + 1)
                        snippet = "".join(
                            f"{i + 1:4d}: {file_lines[i].rstrip()}\n"
                            for i in range(start, end)
                        )
                        context_results.append(
                            f"File: {filename}, Match at line {line_num + 1}\n{snippet}"
                        )
                    except Exception as e:
                        context_results.append(
                            f"{match}\n[Could not read context: {e}]"
                        )

                out_text = (
                    f"Found {len(context_results)} matches (with context):\n\n"
                    "```text\n" + "\n".join(context_results) + "\n```"
                )
                print_to_console(
                    text=out_text[:500] + "...",
                    title=f"Grep search: {query}",
                    border_style=colorscheme.message,
                )
                return out_text
            else:
                return f"No matches found for: {query}"

        except Exception as e:
            return f"Error during text search: {str(e)}"


class ReadFileInput(BaseModel):
    """Input for read file tool."""

    filePath: str = Field(description="The absolute path of the file to read.")
    startLineNumberBaseZero: int = Field(
        description="The line number to start reading from, 0-based."
    )
    endLineNumberBaseZero: int = Field(
        description="The inclusive line number to end reading at, 0-based."
    )


class ReadFileTool(BaseTool):
    """Read the contents of a file."""

    name: str = "read_file"
    description: str = "Read the contents of a file. You must specify the line range you're interested in."
    args_schema: Optional[ArgsSchema] = ReadFileInput

    def _run(
        self, filePath: str, startLineNumberBaseZero: int, endLineNumberBaseZero: int
    ) -> str:
        """Read file contents within the specified line range."""

        try:
            if not os.path.exists(filePath):
                return f"File not found: {filePath}"

            with open(filePath, "r", encoding="utf-8") as file:
                lines = file.readlines()

            # Convert to 0-based indexing
            start = max(0, startLineNumberBaseZero)
            end = min(len(lines), endLineNumberBaseZero + 1)

            if start >= len(lines):
                return f"Start line {startLineNumberBaseZero} is beyond file length ({len(lines)} lines)"

            selected_lines = lines[start:end]

            # Add line numbers
            result_lines = []
            for i, line in enumerate(selected_lines, start=start):
                result_lines.append(f"{i:4d}: {line.rstrip()}")

            total_lines = len(lines)
            return (
                f"File: {filePath} (lines {start}-{end - 1} of {total_lines} total)\n"
                + "\n".join(result_lines)
            )

            print_text = "\n".join(result_lines)
            print_to_console(
                text=print_text[:500] + "...",
                title=f"Read file: {filePath}",
                border_style=colorscheme.message,
            )

        except Exception as e:
            return f"Error reading file: {str(e)}"


@tool("get_working_directory", parse_docstring=True)
def get_working_directory_tool() -> str:
    """
    Get the current working directory.

    Returns:
        str: The current working directory path
    """
    return os.getcwd()


class RunJuliaCodeToolInput(BaseModel):
    code: str = Field(
        description="The Julia code that should be executed",
    )


@tool(
    "run_julia_code",
    args_schema=RunJuliaCodeToolInput,
    description="Execute Julia code. Returns output or error message.",
)
def run_julia_code_tool(code: str):
    code = fix_imports(code)
    code = shorter_simulations(code)
    out, code_failed = _run_julia_code(code, print_code=True)
    if code_failed:
        return out
    return "Code executed successfully!"


class RunJuliaLinterToolInput(BaseModel):
    code: str = Field(
        description="The Julia code that should be analyzed using the linter",
    )


@tool(
    "run_julia_linter",
    args_schema=RunJuliaLinterToolInput,
    description="Run a static analysis of Julia code using a linter.",
)
def run_julia_linter_tool(code: str):
    out, code_failed = _run_linter(code)
    if not code_failed:
        return out
    return "Linter found no issues!"
