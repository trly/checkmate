"""Confirmation modal screen."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmScreen(ModalScreen[bool]):
    """A modal screen for confirming actions."""

    BINDINGS: ClassVar[list] = [
        ("escape", "cancel", "Cancel"),
        ("y", "confirm", "Confirm"),
        ("n", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
        background: $surface 50%;
    }

    ConfirmScreen > Container {
        width: auto;
        min-width: 40;
        height: auto;
        padding: 1 2;
        background: $panel;
        border: thick $accent;
    }

    ConfirmScreen Label#message {
        width: 100%;
        content-align: center middle;
        margin: 1 0 2 0;
        text-style: bold;
    }

    ConfirmScreen Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
    }

    ConfirmScreen Button {
        margin: 0 1;
    }
    """

    def __init__(self, message: str = "Are you sure?"):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.message, id="message")
            with Horizontal():
                yield Button("Yes", variant="primary", id="yes-btn")
                yield Button("No", variant="error", id="no-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
