"""Sort selection modal screen component."""

from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label


class SortSelectScreen(Screen):
    """Modal screen for selecting a sort attribute."""

    BINDINGS: ClassVar[list] = [
        ("escape", "cancel", "Cancel"),
    ]

    DEFAULT_CSS = """
    SortSelectScreen {
        background: $surface;
    }
    
    SortSelectScreen > Container {
        width: auto;
        height: auto;
        border: solid $accent;
        background: $panel;
        padding: 2 3;
        align: center middle;
    }
    
    SortSelectScreen Label#title {
        width: 100%;
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
    }
    
    SortSelectScreen .button-group {
        width: 1fr;
        height: auto;
    }
    
    SortSelectScreen Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    SortSelectScreen Button:last-of-type {
        margin-bottom: 0;
    }
    """

    def __init__(self, callback=None):
        """Initialize the sort selection screen.

        Args:
            callback: Function to call with selected sort attribute when a
                button is pressed. Callback receives attribute name as string:
                'priority', 'context', 'project', 'due', 'created'
        """
        super().__init__()
        self.callback = callback

    def compose(self) -> ComposeResult:
        """Create the sort selection screen."""
        with Container():
            yield Label("Select sort attribute", id="title")

            with Vertical(classes="button-group"):
                yield Button("Priority (A-Z)", id="sort-priority-btn")
                yield Button("Context (@-tags)", id="sort-context-btn")
                yield Button("Project (+projects)", id="sort-project-btn")
                yield Button("Due Date", id="sort-due-btn")
                yield Button("Created Date", id="sort-created-btn")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        # Map button IDs to sort attributes
        button_to_attribute = {
            "sort-priority-btn": "priority",
            "sort-context-btn": "context",
            "sort-project-btn": "project",
            "sort-due-btn": "due",
            "sort-created-btn": "created",
        }

        if button_id in button_to_attribute:
            attribute = button_to_attribute[button_id]
            if self.callback:
                self.callback(attribute)
            self.dismiss()

    def action_cancel(self) -> None:
        """Cancel the screen without applying sort."""
        self.dismiss()
