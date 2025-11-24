"""Task creation/editing screen component."""

from datetime import datetime
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Resize
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, Static

from ..models import Task
from ..services import TodoService


class TaskFormSection(Static):
    """A labeled form field section."""

    DEFAULT_CSS = """
    TaskFormSection {
        width: 100%;
        height: auto;
        margin: 1 0;
    }
    
    TaskFormSection Label {
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    
    TaskFormSection Input {
        width: 100%;
    }
    """


class ResponsiveButtonGroup(Static):
    """Container for buttons that stacks vertically when space is tight."""

    is_vertical = reactive(False, recompose=True)

    DEFAULT_CSS = """
    ResponsiveButtonGroup {
        width: 100%;
        height: auto;
        margin-top: 2;
    }
    
    ResponsiveButtonGroup Button {
        margin-right: 1;
    }
    
    ResponsiveButtonGroup.vertical Button {
        width: 100%;
        margin: 0 0 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Create button container with appropriate layout."""
        if self.is_vertical:
            container = Vertical(id="button-container")
        else:
            container = Horizontal(id="button-container")

        with container:
            yield Button("Submit", id="submit-btn", variant="primary")
            yield Button("Cancel", id="cancel-btn", variant="default")

    def watch_is_vertical(self, value: bool) -> None:
        """Update CSS class when layout changes."""
        if value:
            self.add_class("vertical")
        else:
            self.remove_class("vertical")

    def on_mount(self) -> None:
        """Check initial size and update layout."""
        self._check_layout()

    def on_resize(self, event: Resize) -> None:
        """Respond to size changes."""
        self._check_layout()

    def _check_layout(self) -> None:
        """Determine if buttons should stack vertically."""
        # Available width for buttons (accounting for padding)
        available_width = self.size.width - 4  # Account for padding
        # Estimate needed width: 2 buttons at ~10 chars each + spacing
        needed_width = 28

        should_be_vertical = available_width < needed_width

        if self.is_vertical != should_be_vertical:
            self.is_vertical = should_be_vertical


class CreateTaskScreen(Screen):
    """Screen for creating a new task or editing an existing one."""

    BINDINGS: ClassVar[list] = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Submit"),
    ]

    DEFAULT_CSS = """
    CreateTaskScreen {
        background: $surface;
    }
    
    CreateTaskScreen > Container {
        width: 100%;
        height: auto;
        border: solid $accent;
        background: $panel;
        padding: 2 3;
    }
    
    CreateTaskScreen Label#title {
        width: 100%;
        text-align: center;
        text-style: bold;
        margin-bottom: 2;
    }
    
    CreateTaskScreen .form-section {
        width: 100%;
        height: auto;
        margin: 1 0;
    }
    
    CreateTaskScreen .priority-section {
        width: 100%;
        height: auto;
        margin: 1 0;
    }
    
    CreateTaskScreen .priority-section Label {
        width: 100%;
        margin-bottom: 1;
        text-style: bold;
    }
    
    CreateTaskScreen #priority-input {
        width: 100%;
    }
    """

    def __init__(self, service: TodoService, task: Task | None = None):
        super().__init__()
        self.service = service
        self.editing_task = task

    def compose(self) -> ComposeResult:
        title = "Edit Task" if self.editing_task else "Create New Task"

        with Container():
            yield Label(title, id="title")

            # Description field
            with Vertical(classes="form-section"):
                yield Label("Description")
                yield Input(id="task-input", placeholder="Enter task description")

            # Priority field
            with Vertical(classes="priority-section"):
                yield Label("Priority (A-Z)")
                yield Input(id="priority-input", max_length=1, placeholder="Optional")

            # Due date field
            with Vertical(classes="form-section"):
                yield Label("Due date (YYYY-MM-DD)")
                yield Input(id="due-input", placeholder="Optional")

            # Buttons (responsive)
            yield ResponsiveButtonGroup()

        yield Footer()

    def on_mount(self) -> None:
        """Focus description input on mount and prepopulate if editing."""
        task_input = self.query_one("#task-input", Input)
        priority_input = self.query_one("#priority-input", Input)
        due_input = self.query_one("#due-input", Input)

        # Prepopulate fields if editing
        if self.editing_task:
            task_input.value = self.editing_task.description
            if self.editing_task.priority:
                priority_input.value = self.editing_task.priority
            # Extract due date
            if self.editing_task.due_date:
                due_input.value = self.editing_task.due_date.strftime("%Y-%m-%d")

        task_input.focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        if event.input.id == "task-input":
            self.action_submit()

    def action_submit(self) -> None:
        """Submit the task."""

        priority_input = self.query_one("#priority-input", Input)
        task_input = self.query_one("#task-input", Input)
        due_input = self.query_one("#due-input", Input)

        priority = priority_input.value.strip() or None
        task_text = task_input.value.strip()
        due_date = due_input.value.strip() or None
        
        parsed_due_date = None
        if due_date:
            try:
                parsed_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
            except ValueError:
                self.notify("Date must be in YYYY-MM-DD format", severity="error")
                due_input.focus()
                return

        if not task_text:
            self.notify("Task description cannot be empty", severity="error")
            task_input.focus()
            return

        try:
            if self.editing_task:
                # Update task
                self.service.update_task(
                    self.editing_task,
                    description=task_text,
                    priority=priority,
                    due_date=parsed_due_date,
                )
                # We return the updated task description for notification
                self.dismiss(
                    result={
                        "success": True,
                        "task": self.editing_task.description,
                        "mode": "edit",
                    }
                )
            else:
                # Create new task
                new_task = self.service.create_task(
                    description=task_text, priority=priority, due_date=parsed_due_date
                )
                self.dismiss(
                    result={
                        "success": True,
                        "task": new_task.description,
                        "mode": "create",
                    }
                )
        except ValueError as e:
            self.notify(str(e), severity="error")
            # Focus appropriate field based on error message?
            if "Priority" in str(e):
                priority_input.focus()
        except Exception as e:
            self.notify(f"Error: {e!s}", severity="error")

    def action_cancel(self) -> None:
        """Cancel the screen."""
        self.dismiss(result={"success": False, "cancelled": True})
