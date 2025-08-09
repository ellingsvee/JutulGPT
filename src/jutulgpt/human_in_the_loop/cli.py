from typing import Callable, List

from langchain_core.documents import Document
from rich.prompt import Prompt
from rich.table import Table

import jutulgpt.cli.cli_utils as utils
import jutulgpt.state as state
from jutulgpt.cli.cli_colorscheme import colorscheme
from jutulgpt.globals import console
from jutulgpt.rag.utils import modify_doc_content
from jutulgpt.utils import add_julia_context


def response_on_rag(
    docs: List[Document],
    get_file_source: Callable,
    get_section_path: Callable,
    format_doc: Callable,
    action_name: str = "Modify retrieved documents",
    edit_julia_file: bool = False,
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
        content_within_julia = (
            content if not edit_julia_file else f"```julia\n{content.strip()}\n```"
        )

        # Create a table to show document info
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        table.add_row("Document", f"{i + 1}/{len(docs)}")
        table.add_row("Source", file_source)
        table.add_row("Section", section_path)

        console.print(f"\n{table}")
        utils.print_to_console(
            text=content_within_julia[:500] + "..."
            if len(content_within_julia) > 500
            else content_within_julia,
            title="Content",
            border_style=colorscheme.human_interaction,
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
            utils.print_to_console(
                text=content_within_julia,
                title="Full Document Content",
                border_style=colorscheme.success,
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
                new_content = utils.edit_document_content(
                    content, edit_julia_file=edit_julia_file
                )
                if new_content.strip():
                    if edit_julia_file:
                        new_content = f"```julia\n{new_content.strip()}\n```"
                    filtered_docs.append(modify_doc_content(doc, new_content))
                    console.print("[green]✓ Document edited and kept[/green]")
                else:
                    console.print("[red]✗ Document removed (empty content)[/red]")
            else:  # doc_choice == "s"
                console.print("[red]✗ Document skipped[/red]")

        elif doc_choice == "e":
            new_content = utils.edit_document_content(
                content, edit_julia_file=edit_julia_file
            )
            if new_content.strip():
                if edit_julia_file:
                    new_content = f"```julia\n{new_content.strip()}\n```"
                filtered_docs.append(modify_doc_content(doc, new_content))
                console.print("[green]✓ Document edited and kept[/green]")
            else:
                console.print("[red]✗ Document removed (empty content)[/red]")

    console.print(
        f"\n[bold]Summary:[/bold] Kept {len(filtered_docs)}/{len(docs)} documents"
    )
    return filtered_docs


def response_on_check_code(code: str) -> tuple[bool, str, str]:
    """
    Returns:
        bool: Whether the user wants to check the code or not
        str: Additional feedback to the model
    """
    console.print("\n[bold yellow]Code check[/bold yellow]")

    console.print("Do you want to check the code for any potential errors?")
    console.print("1. Check the code")
    console.print("2. Give feedback to model")
    console.print("3. Edit the code manually")
    console.print("4. Skip code check")

    choice = Prompt.ask("Your choice", choices=["1", "2", "3", "4"], default="1")

    if choice == "1":
        console.print("[green]✓ Running code checks[/green]")
        return True, "", code
    elif choice == "2":
        console.print("[bold blue]Give feedback:[/bold blue] ")
        user_input = console.input("> ")
        if not user_input.strip():  # If the user input is empty
            console.print("[red]✗ User feedback empty[/red]")
            return False, "", code
        console.print("[green]✓ Feedback recieved[/green]")
        return False, user_input, code
    elif choice == "3":
        console.print("\n[bold]Edit Code[/bold]")
        new_code = utils.edit_document_content(code, edit_julia_file=True)

        if new_code.strip():
            utils.print_to_console(
                text=add_julia_context(new_code),
                title="Code update",
                border_style=colorscheme.message,
            )
            console.print("[green]✓ Code updated[/green]")
            return True, "", new_code
        console.print("[red]✓ Code empty. Not updating![/red]")
        return True, "", code

    else:  # choice == "4"
        console.print("[red]✗ Skipping code checks[/red]")
        return False, "", code


def response_on_error() -> tuple[bool, str]:
    """
    Returns:
        bool: Whether the user wants to check the code or not
        str: Additional feedback to the model
    """
    console.print("\n[bold red]Code check failed[/bold red]")

    console.print("What do you want to do?")
    console.print("1. Try to fix the code")
    console.print("2. Give extra feedback to the model on what might be wrong")
    console.print("3. Skip code fixing")

    choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    if choice == "1":
        console.print("[green]✓ Trying to fix code[/green]")
        return True, ""
    elif choice == "2":
        console.print("[bold blue]Give feedback:[/bold blue]")
        user_input = console.input("> ")
        if not user_input.strip():  # If the user input is empty
            console.print("[red]✗ User feedback empty[/red]")
            return True, ""
        console.print("[green]✓ Feedback received[/green]")
        return True, user_input
    else:  # choice == "3"
        console.print("[red]✗ Skipping code fix[/red]")
        return False, ""


def modify_rag_query(query: str, retriever_name: str) -> str:
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

    utils.print_to_console(
        text=f"**Original Query:** `{query}`",
        title=f"Retrieving from {retriever_name}",
        border_style=colorscheme.warning,
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
        new_query = utils.edit_document_content(query)

        if new_query.strip():
            console.print(f"[green]✓ Query updated for {retriever_name}[/green]")
            utils.print_to_console(
                text=f"**New Query:** `{new_query.strip()}`",
                title="Updated Query",
                border_style=colorscheme.success,
            )

            return new_query.strip()
        else:
            console.print("[yellow]⚠ Empty query, using original[/yellow]")
            return query
    else:  # choice == "3"
        console.print(f"[red]✗ Skipping {retriever_name} retrieval[/red]")
        return ""  # Return empty string to indicate no query


def handle_code_response(response_content: str) -> None:
    """
    CLI interaction for handling code found in multi-agent responses.
    Allows user to run the code and/or save it to a file.

    Args:
        console: Rich console for display
        response_content: The response content that may contain code
    """
    from jutulgpt.utils import get_code_from_response

    # Extract code from the response
    code_block = get_code_from_response(response_content)

    # If no code found, return early
    if not code_block.imports and not code_block.code:
        return

    # Display the found code
    full_code = code_block.get_full_code(within_julia_context=True)

    console.print("\n[bold yellow]Code Detected in Response[/bold yellow]")
    console.print("\nWould you like to save the code (y/n)?")

    choice = Prompt.ask("Your choice", choices=["y", "n"], default="n")

    # Run the code if requested

    # Save the code if requested
    if choice == "y":
        utils.save_code_to_file(code_block)
    else:  # choice == "n"
        console.print("[blue]ℹ No action taken[/blue]")


def response_on_generated_code(code_block) -> tuple[state.CodeBlock, bool, str]:
    """

    Returns:
        CodeBlock: The potentially modified code block
        bool: Whether the code block was updated (True) or not (False)
        str: Any user feedback to send back to the agent
    """
    from jutulgpt.utils import get_code_from_response

    # If there is no code to edit, return immediately
    if code_block.is_empty():
        return code_block, False, ""

    # Format the code for display
    full_code = code_block.get_full_code(within_julia_context=True)

    console.print("\n[bold yellow]Generated Code Review[/bold yellow]")

    utils.print_to_console(
        text=full_code,
        title="Coding Agent",
        border_style=colorscheme.human_interaction,
    )

    console.print("\nWhat would you like to do with this code?")
    console.print("1. Accept code")
    console.print("2. Give feedback to agent and regenerate code")
    console.print("3. Edit the code manually")

    choice = Prompt.ask("Your choice", choices=["1", "2", "3"], default="1")

    if choice == "1":
        console.print("[green]✓ Code accepted[/green]")
        return code_block, False, ""
    elif choice == "2":
        console.print("[bold blue]Give feedback:[/bold blue] ")
        user_input = console.input("> ")
        if not user_input.strip():  # If the user input is empty
            console.print("[red]✗ User feedback empty[/red]")
            return code_block, False, ""
        return code_block, False, user_input

    else:  # choice == "3":
        console.print("\n[bold]Edit Code[/bold]")
        new_code = utils.edit_document_content(
            code_block.get_full_code(within_julia_context=False), edit_julia_file=True
        )

        if new_code.strip():
            utils.print_to_console(
                text=add_julia_context(new_code),
                title="Code update",
                border_style=colorscheme.message,
            )
            # Update the code block with the new code
            updated_code_block = get_code_from_response(
                new_code, within_julia_context=False
            )
            console.print("[green]✓ Code updated[/green]")
            return updated_code_block, True, ""
        else:
            console.print("[red]✗ Empty code provided[/red]")
            return code_block, False, ""
