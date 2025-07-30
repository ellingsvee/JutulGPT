from typing import Callable, List

from langchain_core.documents import Document
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from jutulgpt.rag.utils import modify_doc_content

console = Console()


def print_to_console(
    text: str,
    title: str = "Assistant",
    border_style: str = "",
    panel_kwargs: dict = {},
    with_markdown: bool = True,
):
    """
    Print text to the console with a panel.

    Args:
        console (Console): The console to print to.
        text (str): The text to print.
        title (str): The title of the panel.
        panel_kwargs (dict): Additional keyword arguments for the panel.
    """
    if border_style != "":
        panel_kwargs["border_style"] = border_style
    if title != "":
        panel_kwargs["title"] = title

    if with_markdown:
        console.print(Panel.fit(Markdown(text), **panel_kwargs))
    else:
        console.print(Panel.fit(text, title=title, **panel_kwargs))


def cli_response_on_rag(
    console: Console,
    docs: List[Document],
    get_file_source: Callable,
    get_section_path: Callable,
    format_doc: Callable,
    action_name: str = "Modify retrieved documents",
) -> List[Document]:
    """
    CLI version of response_on_rag that allows interactive document filtering/editing.

    Args:
        console: Rich console for display
        docs: List of retrieved documents
        get_file_source: Function to get the file source of a document
        get_section_path: Function to get the section path of a document
        format_doc: Function to format a document for display
        action_name: Name of the action for display

    Returns:
        List of documents after user interaction
    """
    if not docs:
        console.print("[yellow]No documents retrieved.[/yellow]")
        return docs

    console.print(f"\n[bold blue]{action_name}[/bold blue]")
    console.print(f"Found {len(docs)} document(s). Choose what to do:")
    console.print("1. Accept all documents")
    console.print("2. Review and filter documents")
    console.print("3. Reject all documents")

    choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    if choice == "1":
        console.print("[green]✓ Accepting all documents[/green]")
        return docs
    elif choice == "3":
        console.print("[red]✗ Rejecting all documents[/red]")
        return []

    # Interactive review mode
    console.print("\n[bold]Document Review Mode[/bold]")
    filtered_docs = []

    for i, doc in enumerate(docs):
        section_path = get_section_path(doc)
        file_source = get_file_source(doc)
        content = format_doc(doc)

        # Create a table to show document info
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        table.add_row("Document", f"{i + 1}/{len(docs)}")
        table.add_row("Source", file_source)
        table.add_row("Section", section_path)

        console.print(f"\n{table}")
        console.print(
            Panel.fit(
                Markdown(content[:500] + "..." if len(content) > 500 else content),
                title="Document Content",
                border_style="blue",
            )
        )

        console.print(
            "\nOptions: [bold](k)[/bold]eep | [bold](e)[/bold]dit | [bold](s)[/bold]kip | [bold](v)[/bold]iew-full"
        )
        doc_choice = Prompt.ask(
            "What to do with this document?", choices=["k", "e", "s", "v"], default="k"
        )

        if doc_choice == "k":
            filtered_docs.append(doc)
            console.print("[green]✓ Document kept[/green]")

        elif doc_choice == "s":
            console.print("[red]✗ Document skipped[/red]")

        elif doc_choice == "v":
            console.print(
                Panel(
                    Markdown(content),
                    title="Full Document Content",
                    border_style="green",
                )
            )
            # Ask again after viewing
            console.print(
                "\nOptions: [bold](k)[/bold]eep | [bold](e)[/bold]dit | [bold](s)[/bold]kip"
            )
            doc_choice = Prompt.ask(
                "Now what to do with this document?",
                choices=["k", "e", "s"],
                default="k",
            )
            if doc_choice == "k":
                filtered_docs.append(doc)
                console.print("[green]✓ Document kept[/green]")
            elif doc_choice == "e":
                new_content = edit_document_content(console, content)
                if new_content.strip():
                    filtered_docs.append(modify_doc_content(doc, new_content))
                    console.print("[green]✓ Document edited and kept[/green]")
                else:
                    console.print("[red]✗ Document removed (empty content)[/red]")
            else:  # doc_choice == "s"
                console.print("[red]✗ Document skipped[/red]")

        elif doc_choice == "e":
            new_content = edit_document_content(console, content)
            if new_content.strip():
                filtered_docs.append(modify_doc_content(doc, new_content))
                console.print("[green]✓ Document edited and kept[/green]")
            else:
                console.print("[red]✗ Document removed (empty content)[/red]")

    console.print(
        f"\n[bold]Summary:[/bold] Kept {len(filtered_docs)}/{len(docs)} documents"
    )
    return filtered_docs


def edit_document_content(console: Console, original_content: str) -> str:
    """
    Allow user to edit document content interactively.

    Args:
        console: Rich console for display
        original_content: The original document content

    Returns:
        The edited content
    """
    console.print("\n[bold]Edit Document Content[/bold]")
    console.print("Choose editing method:")
    console.print("1. Edit in external editor (recommended)")
    console.print("2. Replace with new text (paste mode)")
    console.print("3. Keep original")

    # External editor option
    try:
        import os
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w+", suffix=".md", delete=False) as f:
            f.write(original_content)
            f.flush()

            editor = os.environ.get("EDITOR", "vim")
            try:
                subprocess.run([editor, f.name], check=True)

                with open(f.name, "r") as edited_file:
                    edited_content = edited_file.read()

                os.unlink(f.name)
                return edited_content

            except subprocess.CalledProcessError:
                console.print(
                    f"[red]Error opening editor '{editor}'. Falling back to original content.[/red]"
                )
                os.unlink(f.name)
                return original_content
            except FileNotFoundError:
                console.print(
                    f"[red]Editor '{editor}' not found. Try setting EDITOR environment variable.[/red]"
                )
                os.unlink(f.name)
                return original_content

    except Exception as e:
        console.print(f"[red]Error with external editor: {e}[/red]")
        return original_content


def cli_response_on_check_code(console: Console, code_block) -> tuple:
    """
    CLI version of response_on_check_code that allows interactive code review and editing.

    Args:
        console: Rich console for display
        code_block: The CodeBlock object to potentially modify or accept

    Returns:
        tuple: (code_block, check_code_bool, extra_messages)
            - code_block: The potentially modified code block
            - check_code_bool: Whether to check the code (True) or ignore it (False)
            - extra_messages: List of AI messages to add to state
    """

    from jutulgpt.utils import get_code_from_response

    # If there is no code to edit, return immediately
    if not code_block.imports and not code_block.code:
        return code_block, False, []

    # Format the code for display
    full_code = code_block.get_full_code(within_julia_context=True)

    console.print("\n[bold yellow]Generated Code Review[/bold yellow]")
    console.print(
        Panel(
            Markdown(full_code),
            title="Human Interaction",
            border_style="blue",
        )
    )

    console.print("\nWhat would you like to do with this code?")
    console.print("1. Accept and run the code")
    console.print("2. Edit the code before running")
    console.print("3. Skip code execution")

    choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    if choice == "1":
        console.print("[green]✓ Code accepted for execution[/green]")
        return code_block, True, []

    elif choice == "2":
        console.print("\n[bold]Edit Code[/bold]")
        new_code = edit_document_content(console, full_code)

        if new_code.strip():
            # Create message about the user's update
            #             message_content = f"""The code was updated by the user. The following is what will be run and checked:
            # {new_code}
            # """
            # Update the code block with the new code
            updated_code_block = get_code_from_response(new_code)
            console.print("[green]✓ Code updated and will be executed[/green]")
            # return updated_code_block, True, [AIMessage(content=message_content)]
            return updated_code_block, True, []
        else:
            console.print("[red]✗ Empty code provided, skipping execution[/red]")
            return code_block, False, []

    else:  # choice == "3"
        console.print("[red]✗ Code execution skipped[/red]")
        return code_block, False, []


def cli_modify_rag_query(console: Console, query: str, retriever_name: str) -> str:
    """
    CLI version of modify_rag_query that allows interactive query modification.

    Args:
        console: Rich console for display
        query: The original query string
        retriever_name: Name of the retriever (e.g., "JutulDarcy", "Fimbul")

    Returns:
        str: The potentially modified query
    """
    console.print(f"\n[bold yellow]{retriever_name} Query Review[/bold yellow]")
    console.print(
        Panel(
            Markdown(f"**Original Query:** `{query}`"),
            title=f"Retrieving from {retriever_name}",
            border_style="blue",
        )
    )

    console.print("\nWhat would you like to do with this query?")
    console.print("1. Accept the query as-is")
    console.print("2. Edit the query")
    console.print("3. Skip retrieval completely")

    choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    if choice == "1":
        console.print(f"[green]✓ Using original query for {retriever_name}[/green]")
        return query

    elif choice == "2":
        new_query = edit_document_content(console, query)

        if new_query.strip():
            console.print(f"[green]✓ Query updated for {retriever_name}[/green]")
            console.print(
                Panel(
                    Markdown(f"**New Query:** `{new_query.strip()}`"),
                    title="Updated Query",
                    border_style="green",
                )
            )
            return new_query.strip()
        else:
            console.print("[yellow]⚠ Empty query, using original[/yellow]")
            return query
    else:  # choice == "3"
        console.print(f"[red]✗ Skipping {retriever_name} retrieval[/red]")
        return ""  # Return empty string to indicate no query


def cli_response_on_error_analysis(console: Console, error_analysis: str) -> str:
    """
    CLI version of error analysis review that allows interactive acceptance, modification, or rejection.

    Args:
        console: Rich console for display
        error_analysis: The AI-generated error analysis message

    Returns:
        str: The potentially modified error analysis, or empty string if rejected
    """
    console.print("\n[bold yellow]Error Analysis Generated[/bold yellow]")
    console.print(
        Panel(
            Markdown(error_analysis),
            title="AI Error Analysis",
            border_style="magenta",
        )
    )

    console.print("\nWhat would you like to do with this error analysis?")
    console.print("1. Accept the analysis as-is")
    console.print("2. Edit/modify the analysis")
    console.print("3. Skip error analysis completely")

    choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    if choice == "1":
        console.print("[green]✓ Error analysis accepted[/green]")
        return error_analysis

    elif choice == "2":
        console.print("\n[bold]Edit Error Analysis[/bold]")
        new_analysis = edit_document_content(console, error_analysis)

        if new_analysis.strip():
            console.print("[green]✓ Error analysis updated[/green]")
            console.print(
                Panel(
                    Markdown(new_analysis.strip()),
                    title="Updated Error Analysis",
                    border_style="green",
                )
            )
            return new_analysis.strip()
        else:
            console.print("[yellow]⚠ Empty analysis, using original[/yellow]")
            return error_analysis

    else:  # choice == "3"
        console.print("[red]✗ Error analysis skipped[/red]")
        return ""  # Return empty string to indicate no analysis
