"""Checkmate - A terminal user interface client for todos.txt files."""

import sys
from typing import ClassVar

from textual.app import App

from .config import discover_files, load_config_file
from .repository import FileTaskRepository
from .screens import TodoListScreen
from .services import TodoService

# CSS for responsive layout
TODOS_CSS = """
#todos-container {
    height: 1fr;
    width: 100%;
}
"""


class CheckmateApp(App):
    TITLE = "Checkmate"
    CSS = TODOS_CSS

    BINDINGS: ClassVar[list] = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self, service: TodoService):
        super().__init__()
        self.service = service

    async def on_mount(self) -> None:
        """Push the main screen when the app starts."""
        await self.push_screen(TodoListScreen(service=self.service))


def parse_args():
    """Parse command-line arguments"""
    todo_file = None
    done_file = None

    # Simple argument parsing
    for arg in sys.argv[1:]:
        if arg.startswith("--todo="):
            todo_file = arg.split("=", 1)[1]
        elif arg.startswith("--done="):
            done_file = arg.split("=", 1)[1]
        elif arg in ("-h", "--help"):
            print("Usage: checkmate [OPTIONS]")
            print("Options:")
            print("  --todo=FILE   Path to todo.txt file")
            print("  --done=FILE   Path to done.txt file")
            print("  -h, --help    Show this help message")
            sys.exit(0)

    return todo_file, done_file


def main():
    # Parse command-line arguments
    cli_todo, cli_done = parse_args()

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


if __name__ == "__main__":
    main()
