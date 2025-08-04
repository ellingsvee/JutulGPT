from __future__ import annotations

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from jutulgpt.globals import console

# from jutulgpt.nodes import check_code
from jutulgpt.state import State


def get_user_input(state: State, config: RunnableConfig):
    console.print("[bold blue]User Input:[/bold blue] ")
    user_input = console.input("> ")

    # Check for quit command
    if user_input.strip().lower() in ["q", "exit", "quit", "quit()", "exit()"]:
        console.print("[bold red]Goodbye![/bold red]")
        exit(0)

    return {"messages": [HumanMessage(content=user_input)]}
