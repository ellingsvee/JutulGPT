from __future__ import annotations

import os
import re
import subprocess
from typing import Optional

from langchain_core.tools import BaseTool, tool
from langchain_core.tools.base import ArgsSchema
from pydantic import BaseModel, Field

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.nodes.check_code import _run_julia_code, _run_linter, _shorter_simulations


class SemanticSearchInput(BaseModel):
    """Input for semantic search tool."""

    query: str = Field(
        description="The query to search the codebase for. Should contain all relevant context."
    )


class SemanticSearchTool(BaseTool):
    """Run a natural language search for relevant code or documentation comments."""

    name: str = "semantic_search"
    description: str = "Run a natural language search for relevant code or documentation from JutulDarcy."
    args_schema: Optional[ArgsSchema] = SemanticSearchInput

    def _run(self, query: str) -> str:
        """Run semantic search on the workspace."""
        try:
            # Simple implementation using grep with keyword extraction
            workspace_path = "./src/jutulgpt/rag/jutuldarcy/"

            # Extract potential keywords from the query
            keywords = re.findall(r"\b\w+\b", query.lower())

            results = []
            for keyword in keywords[:5]:  # Limit to top 5 keywords
                try:
                    # Search for the keyword in common code file types
                    cmd = f"grep -r -n -i --include='*.py' --include='*.jl' --include='*.js' --include='*.ts' --include='*.md' '{keyword}' {workspace_path}"
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True, timeout=10
                    )
                    if result.stdout:
                        results.extend(
                            result.stdout.strip().split("\n")[:10]
                        )  # Limit results per keyword
                except subprocess.TimeoutExpired:
                    continue

            if results:
                out_text = (
                    f"Found {len(results)} relevant matches:\n\n"
                    "```text\n" + "\n".join(results[:20]) + "\n```"
                )

                print_to_console(
                    text=out_text,
                    title=f"Semantic search: {query}",
                    border_style=colorscheme.message,
                )
                return out_text

            else:
                return f"No relevant code found for query: {query}"

        except Exception as e:
            return f"Error during semantic search: {str(e)}"


class GrepSearchInput(BaseModel):
    """Input for grep search tool."""

    query: str = Field(
        description="The pattern to search for in files. Can be a regex or plain text pattern"
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
    description: str = (
        "Do a text search in the JutulDarcy documentation. Limited to 20 results."
    )
    args_schema: Optional[ArgsSchema] = GrepSearchInput

    def _run(
        self,
        query: str,
        includePattern: Optional[str] = None,
        isRegexp: Optional[bool] = False,
    ) -> str:
        """Search for text in files."""

        # print_to_console(
        #     text=f"query: {query}, includePattern: {includePattern}, isRegexp: {isRegexp}",
        #     title=f"Tool invoked: {self.name}",
        #     border_style=colorscheme.message,
        # )

        try:
            workspace_path = "./src/jutulgpt/rag/jutuldarcy/"

            # Build grep command
            cmd_parts = ["grep", "-r", "-n"]

            if isRegexp:
                cmd_parts.append("-E")
            else:
                cmd_parts.append("-F")  # Fixed string search

            # Add include pattern if specified
            if includePattern:
                cmd_parts.extend(["--include", includePattern])
            else:
                # Default to common code file types
                cmd_parts.extend(
                    [
                        "--include=*.py",
                        "--include=*.jl",
                        "--include=*.js",
                        "--include=*.ts",
                        "--include=*.md",
                    ]
                )

            cmd_parts.extend([query, workspace_path])

            result = subprocess.run(
                cmd_parts, capture_output=True, text=True, timeout=10
            )

            if result.stdout:
                # lines = result.stdout.strip().split("\n")[:20]  # Limit to 20 results
                # out_text = f"Found {len(lines)} matches:\n" + "\n".join(lines)

                lines = result.stdout.strip().split("\n")[:20]  # Limit to 20 results
                out_text = (
                    f"Found {len(lines)} matches:\n\n"
                    "```text\n" + "\n".join(lines) + "\n```"
                )
                print_to_console(
                    text=out_text,
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


def _fix_imports(code: str) -> str:
    required_imports = ["Fimbul", "GLMakie"]
    if not all(pkg in code for pkg in required_imports):
        return code
    return 'using Pkg; Pkg.activate(".");\n' + code


@tool(
    "run_julia_code",
    args_schema=RunJuliaCodeToolInput,
    description="Execute Julia code. Returns output or error message.",
)
def run_julia_code_tool(code: str):
    code = _fix_imports(code)
    code = _shorter_simulations(code)
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
