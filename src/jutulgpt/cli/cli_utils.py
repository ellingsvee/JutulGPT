from typing import List, Optional

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from rich.align import Align
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from jutulgpt.globals import console
from jutulgpt.state import CodeBlock


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

    console.print(Panel.fit(Markdown(text) if with_markdown else text, **panel_kwargs))


def stream_to_console(
    llm,
    message_list: List,
    config: RunnableConfig,
    title: Optional[str] = "",
    border_style: str = "",
    panel_kwargs: dict = {},
    with_markdown: bool = True,
) -> AIMessage:
    ai_message: AIMessage = None
    streamed_text: str = ""
    panel_kwargs = panel_kwargs.copy()  # prevent mutation

    if border_style:
        panel_kwargs["border_style"] = border_style
    if title:
        panel_kwargs["title"] = title

    # Stream the chunks, but don't create Live until the first meaningful one
    stream = llm.stream(message_list, config=config)

    for chunk in stream:
        if chunk.content:
            streamed_text += chunk.content
            ai_message = chunk if ai_message is None else ai_message + chunk

            # Now that we have some content, start the Live panel
            with Live(
                Panel(
                    Markdown(streamed_text) if with_markdown else streamed_text,
                    **panel_kwargs,
                ),
                console=console,
                refresh_per_second=4,
            ) as live:
                for chunk in stream:
                    ai_message += chunk
                    if chunk.content:
                        streamed_text += chunk.content
                        live.update(
                            Panel.fit(
                                Markdown(streamed_text)
                                if with_markdown
                                else streamed_text,
                                **panel_kwargs,
                            )
                        )
            break  # We've handled all remaining chunks inside the Live context
        elif ai_message is None:
            ai_message = chunk
        else:
            ai_message += chunk

    return ai_message


def show_startup_screen():
    subtitle = Text(
        "SINTEF Digital's AI Assistant for JutulDarcy",
        justify="center",
        style="italic green",
    )

    info_text = Text.from_markup(
        "\n[bold cyan]Type your prompt below, or type [yellow]'q'[/yellow] to quit.[/bold cyan]"
    )

    ascii_art = Text.from_markup(
        "[bold green]"
        "     ██╗██╗   ██╗████████╗██╗   ██╗██╗      ██████╗ ██████╗ ████████╗\n"
        "     ██║██║   ██║╚══██╔══╝██║   ██║██║     ██╔════╝ ██╔══██╗╚══██╔══╝\n"
        "     ██║██║   ██║   ██║   ██║   ██║██║     ██║  ███╗██████╔╝   ██║   \n"
        "██   ██║██║   ██║   ██║   ██║   ██║██║     ██║   ██║██╔═══╝    ██║   \n"
        "╚█████╔╝╚██████╔╝   ██║   ╚██████╔╝███████╗╚██████╔╝██║        ██║   \n"
        " ╚════╝  ╚═════╝    ╚═╝    ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝        ╚═╝   \n"
        "[/bold green]"
    )

    content = Group(
        Align.center(ascii_art),
        Align.center(subtitle),
        Align.center(info_text),
    )

    panel = Panel.fit(
        content,
        border_style="green",
        padding=(1, 4),
        title="",
        title_align="left",
    )
    console.print(panel)


def edit_document_content(original_content: str, edit_julia_file: bool = False) -> str:
    """
    Allow user to edit document content interactively.

    Args:
        console: Rich console for display
        original_content: The original document content

    Returns:
        The edited content
    """
    # External editor option
    file_suffix = ".jl" if edit_julia_file else ".md"
    try:
        import os
        import subprocess
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=file_suffix, delete=False
        ) as f:
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


def save_code_to_file(code_block: CodeBlock) -> None:
    """
    Helper function to save code block to file with user interaction.

    Args:
        code_block: The code block to save
    """
    import os

    console.print("\n[bold yellow]Save Code to File[/bold yellow]")

    # Ask for filename
    default_filename = "generated_code.jl"
    filename = Prompt.ask("Enter filename", default=default_filename)

    # Ensure .jl extension
    if not filename.endswith(".jl"):
        filename += ".jl"

    try:
        # Check if file exists and ask for confirmation
        if os.path.exists(filename):
            overwrite = Prompt.ask(
                f"File '{filename}' already exists. Overwrite?",
                choices=["y", "n"],
                default="n",
            )
            if overwrite.lower() != "y":
                console.print("[yellow]⚠ File save cancelled[/yellow]")
                return

        # Write the code to file
        with open(filename, "w") as f:
            if code_block.imports:
                f.write(code_block.imports + "\n\n")
            f.write(code_block.code)

        console.print(f"[green]✓ Code saved to '{filename}' successfully[/green]")

    except Exception as e:
        console.print(f"[red]✗ Error saving file: {str(e)}[/red]")
