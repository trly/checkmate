"""Checkmate - A terminal user interface client for todos.txt files."""

import argparse
import sys
from typing import ClassVar

from textual.app import App

from .config import discover_files, load_config_file
from .repository import FileTaskRepository
from .screens import TodoListScreen
from .services import TodoService


class CheckmateApp(App):
    TITLE = "Checkmate"
    CSS_PATH = "checkmate.tcss"

    BINDINGS: ClassVar[list] = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, service: TodoService):
        super().__init__()
        self.service = service

    async def on_mount(self) -> None:
        """Push the main screen when the app starts."""
        await self.push_screen(TodoListScreen())


def parse_args() -> tuple[str | None, str | None]:
    """Parse command-line arguments.

    Returns:
        Tuple of (todo_file, done_file) paths.
    """
    parser = argparse.ArgumentParser(
        description="Checkmate - A terminal user interface client for todos.txt files."
    )
    parser.add_argument("--todo", help="Path to todo.txt file")
    parser.add_argument("--done", help="Path to done.txt file")

    args = parser.parse_args()
    return args.todo, args.done


def main():
    # Parse command-line arguments
    cli_todo, cli_done = parse_args()

    try:
        # Load configuration from .todo/config
        config = load_config_file()

        # Discover file paths with proper precedence
        todo_file, done_file = discover_files(
            cli_todo_file=cli_todo,
            cli_done_file=cli_done,
            config=config,
        )

        # Launch app with discovered file paths
        repository = FileTaskRepository(todo_file=todo_file, done_file=done_file)
        service = TodoService(repository)
        app = CheckmateApp(service=service)
        app.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
