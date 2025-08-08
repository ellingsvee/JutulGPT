"""
LangGraph implementations of VS Code tools for JutulGPT.

This module provides LangGraph tool implementations that mirror the functionality
available in VS Code for GitHub Copilot, enabling similar capabilities in the
iterative agent system.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class SemanticSearchInput(BaseModel):
    """Input for semantic search tool."""

    query: str = Field(
        description="The query to search the codebase for. Should contain all relevant context."
    )


class ListCodeUsagesInput(BaseModel):
    """Input for list code usages tool."""

    symbolName: str = Field(
        description="The name of the symbol, such as a function name, class name, method name, variable name, etc."
    )
    filePaths: Optional[List[str]] = Field(
        default=None,
        description="One or more file paths which likely contain the definition of the symbol.",
    )


class FileSearchInput(BaseModel):
    """Input for file search tool."""

    query: str = Field(
        description="Search for files with names or paths matching this query. Can be a glob pattern."
    )


class GrepSearchInput(BaseModel):
    """Input for grep search tool."""

    query: str = Field(
        description="The pattern to search for in files in the workspace. Can be a regex or plain text pattern"
    )
    includePattern: Optional[str] = Field(
        default=None, description="Search files matching this glob pattern."
    )
    isRegexp: Optional[bool] = Field(
        default=False, description="Whether the pattern is a regex."
    )


class ReadFileInput(BaseModel):
    """Input for read file tool."""

    filePath: str = Field(description="The absolute path of the file to read.")
    startLineNumberBaseZero: int = Field(
        description="The line number to start reading from, 0-based."
    )
    endLineNumberBaseZero: int = Field(
        description="The inclusive line number to end reading at, 0-based."
    )


class ListDirInput(BaseModel):
    """Input for list directory tool."""

    path: str = Field(description="The absolute path to the directory to list.")


class RunInTerminalInput(BaseModel):
    """Input for run in terminal tool."""

    command: str = Field(description="The command to run in the terminal.")
    explanation: str = Field(
        description="A one-sentence description of what the command does."
    )
    isBackground: bool = Field(
        description="Whether the command starts a background process."
    )


# Global storage for background processes
_background_processes = {}
_process_counter = 0


class SemanticSearchTool(BaseTool):
    """Run a natural language search for relevant code or documentation comments."""

    name: str = "semantic_search"
    description: str = "Run a natural language search for relevant code or documentation comments from the user's current workspace."
    args_schema = SemanticSearchInput

    def _run(self, query: str) -> str:
        """Run semantic search on the workspace."""
        try:
            # Simple implementation using grep with keyword extraction
            workspace_path = os.getcwd()

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
                return f"Found {len(results)} relevant matches:\n" + "\n".join(
                    results[:20]
                )
            else:
                return f"No relevant code found for query: {query}"

        except Exception as e:
            return f"Error during semantic search: {str(e)}"


class ListCodeUsagesTool(BaseTool):
    """List all usages of a function, class, method, variable etc."""

    name: str = "list_code_usages"
    description: str = "Request to list all usages (references, definitions, implementations etc) of a function, class, method, variable etc."
    args_schema = ListCodeUsagesInput

    def _run(self, symbolName: str, filePaths: Optional[List[str]] = None) -> str:
        """List all usages of a symbol."""
        try:
            workspace_path = os.getcwd()

            # Search for the symbol in code files
            cmd = f"grep -r -n --include='*.py' --include='*.jl' --include='*.js' --include='*.ts' '{symbolName}' {workspace_path}"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=15
            )

            if result.stdout:
                lines = result.stdout.strip().split("\n")
                return f"Found {len(lines)} usages of '{symbolName}':\n" + "\n".join(
                    lines[:30]
                )
            else:
                return f"No usages found for symbol: {symbolName}"

        except Exception as e:
            return f"Error searching for symbol usages: {str(e)}"


class FileSearchTool(BaseTool):
    """Search for files in the workspace by glob pattern."""

    name: str = "file_search"
    description: str = "Search for files in the workspace by glob pattern. This only returns the paths of matching files."
    args_schema = FileSearchInput

    def _run(self, query: str) -> str:
        """Search for files matching the pattern."""
        try:
            workspace_path = os.getcwd()

            # Convert the query to a proper glob pattern if needed
            if not any(char in query for char in ["*", "?", "[", "]"]):
                # If no glob characters, search for files containing the query string
                pattern = f"**/*{query}*"
            else:
                pattern = query

            # Use glob to find matching files
            matches = glob.glob(os.path.join(workspace_path, pattern), recursive=True)

            # Filter out directories, keep only files
            files = [f for f in matches if os.path.isfile(f)][
                :20
            ]  # Limit to 20 results

            if files:
                # Return relative paths
                relative_files = [os.path.relpath(f, workspace_path) for f in files]
                return f"Found {len(relative_files)} files:\n" + "\n".join(
                    relative_files
                )
            else:
                return f"No files found matching pattern: {query}"

        except Exception as e:
            return f"Error searching for files: {str(e)}"


class GrepSearchTool(BaseTool):
    """Do a text search in the workspace."""

    name: str = "grep_search"
    description: str = "Do a text search in the workspace. Limited to 20 results."
    args_schema = GrepSearchInput

    def _run(
        self,
        query: str,
        includePattern: Optional[str] = None,
        isRegexp: Optional[bool] = False,
    ) -> str:
        """Search for text in files."""
        try:
            workspace_path = os.getcwd()

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
                lines = result.stdout.strip().split("\n")[:20]  # Limit to 20 results
                return f"Found {len(lines)} matches:\n" + "\n".join(lines)
            else:
                return f"No matches found for: {query}"

        except Exception as e:
            return f"Error during text search: {str(e)}"


class ReadFileTool(BaseTool):
    """Read the contents of a file."""

    name: str = "read_file"
    description: str = "Read the contents of a file. You must specify the line range you're interested in."
    args_schema = ReadFileInput

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

        except Exception as e:
            return f"Error reading file: {str(e)}"


class ListDirTool(BaseTool):
    """List the contents of a directory."""

    name: str = "list_dir"
    description: str = (
        "List the contents of a directory. Result will have the name of the child."
    )
    args_schema = ListDirInput

    def _run(self, path: str) -> str:
        """List directory contents."""
        try:
            if not os.path.exists(path):
                return f"Directory not found: {path}"

            if not os.path.isdir(path):
                return f"Path is not a directory: {path}"

            entries = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    entries.append(f"{item}/")
                else:
                    entries.append(item)

            if entries:
                return f"Contents of {path}:\n" + "\n".join(entries)
            else:
                return f"Directory {path} is empty"

        except Exception as e:
            return f"Error listing directory: {str(e)}"


class RunInTerminalTool(BaseTool):
    """Run a shell command in a terminal."""

    name: str = "run_in_terminal"
    description: str = (
        "Run a shell command in a terminal. State is persistent across tool calls."
    )
    args_schema = RunInTerminalInput

    def _run(self, command: str, explanation: str, isBackground: bool) -> str:
        """Run a command in terminal."""
        global _background_processes, _process_counter

        try:
            if isBackground:
                # Start background process
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=os.getcwd(),
                )

                _process_counter += 1
                process_id = f"bg_{_process_counter}"
                _background_processes[process_id] = process

                return f"Background process started (ID: {process_id})\nCommand: {command}\nExplanation: {explanation}\nUse get_terminal_output tool to check output."

            else:
                # Run synchronous command
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.getcwd(),
                )

                output = f"Command: {command}\nExplanation: {explanation}\n"
                output += f"Exit code: {result.returncode}\n"

                if result.stdout:
                    output += f"STDOUT:\n{result.stdout}\n"

                if result.stderr:
                    output += f"STDERR:\n{result.stderr}\n"

                return output

        except subprocess.TimeoutExpired:
            return f"Command timed out after 30 seconds: {command}"
        except Exception as e:
            return f"Error running command: {str(e)}"


# List of basic tools for easy import
BASIC_VSCODE_TOOLS = [
    SemanticSearchTool(),
    ListCodeUsagesTool(),
    FileSearchTool(),
    GrepSearchTool(),
    ReadFileTool(),
    ListDirTool(),
    RunInTerminalTool(),
]
