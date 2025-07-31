from jutulgpt import agent
from jutulgpt.cli.cli_utils import print_to_console

if __name__ == "__main__":
    print_to_console(
        text="[bold green]Welcome to JutulGPT. (Type 'q' to quit)[/bold green]",
        title="",
        with_markdown=False,
    )
    agent.run()
