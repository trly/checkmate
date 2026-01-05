"""Task creation/editing screen component."""

import logging
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from ..main import CheckmateApp

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.events import Key, Resize
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Input, Label, Static, TextArea

from ..exceptions import TaskOperationError, TaskValidationError
from ..models import Task

logger = logging.getLogger(__name__)


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
        padding: 1 2;
    }
    
    CreateTaskScreen Label#title {
        width: 100%;
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        padding-top: 1;
    }
    
    .help-text {
        height: auto;
        width: auto;
    }
    
    .help-text Label {
        width: auto;
        color: $text-disabled;
        text-style: italic;
    }
    
    .help-text .context {
        color: $secondary;
    }
    
    .help-text .project {
        color: $warning;
    }
    
    /* Common form section styling */
    .form-section {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .form-section .main-label {
        width: 100%;
        text-style: bold;
        padding: 0;
        margin: 0;
    }
    
    .form-section .help-text {
        margin: 0 0 1 0;
        padding: 0;
    }
    
    .form-section Input, .form-section TextArea {
        width: 100%;
    }

    #task-input {
        height: 6;
    }
    
    /* Grid row for side-by-side inputs */
    .form-row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    .priority-col {
        width: 14;
        height: auto;
        margin-right: 2;
    }
    
    .due-date-col {
        width: 20;
        height: auto;
    }


    """

    def __init__(self, task: Task | None = None):
        super().__init__()
        self.editing_task = task

    @property
    def app(self) -> CheckmateApp:
        return cast("CheckmateApp", super().app)

    def compose(self) -> ComposeResult:
        title = "Edit Task" if self.editing_task else "Create New Task"

        with Container():
            yield Label(title, id="title")

            # Description field
            with Vertical(classes="form-section"):
                yield Label("Description", classes="main-label")
                with Horizontal(classes="help-text"):
                    yield Label("Use ")
                    yield Label("@context", classes="context")
                    yield Label(" and ")
                    yield Label("+project", classes="project")
                    yield Label(" to organize")
                yield TextArea(id="task-input")

            # Priority and Due date fields in a row
            with Horizontal(classes="form-row"):
                # Priority field
                with Vertical(classes="form-section priority-col"):
                    yield Label("Priority", classes="main-label")
                    yield Label("(A-Z)", classes="help-text")
                    yield Input(id="priority-input", max_length=1, placeholder="A-Z")

                # Due date field
                with Vertical(classes="form-section due-date-col"):
                    yield Label("Due Date", classes="main-label")
                    yield Label("YYYY-MM-DD", classes="help-text")
                    yield Input(id="due-input", placeholder="YYYY-MM-DD")

            # Buttons (responsive)
            yield ResponsiveButtonGroup()

        yield Footer()

    def on_mount(self) -> None:
        """Focus description input on mount and prepopulate if editing."""
        task_input = self.query_one("#task-input", TextArea)
        priority_input = self.query_one("#priority-input", Input)
        due_input = self.query_one("#due-input", Input)

        # Prepopulate fields if editing
        if self.editing_task:
            task_input.text = self.editing_task.description
            if self.editing_task.priority:
                priority_input.value = self.editing_task.priority
            if self.editing_task.due_date:
                due_input.value = self.editing_task.due_date.strftime("%Y-%m-%d")
        else:
            due_input.value = date.today().strftime("%Y-%m-%d")

        task_input.focus()

    def on_key(self, event: Key) -> None:
        """Handle key presses for priority and due date inputs."""
        if not self.focused:
            return

        if self.focused.id == "priority-input" and event.key in ("up", "down"):
            event.stop()
            self._adjust_priority(event.key)
        elif self.focused.id == "due-input" and event.key in (
            "up",
            "down",
            "shift+up",
            "shift+down",
        ):
            event.stop()
            self._adjust_due_date(event.key)

    def _adjust_priority(self, key: str) -> None:
        """Adjust the priority based on key press."""
        priority_input = self.query_one("#priority-input", Input)
        current_value = priority_input.value.strip().upper()

        if not current_value or current_value < "A" or current_value > "Z":
            # Start at A if empty or invalid
            priority_input.value = "A"
            return

        if key == "up":
            # A -> B -> C ... -> Z (wraps to A)
            new_char = chr(ord(current_value) + 1) if current_value < "Z" else "A"
        else:  # down
            # Z -> Y -> X ... -> A (wraps to Z)
            new_char = chr(ord(current_value) - 1) if current_value > "A" else "Z"

        priority_input.value = new_char

    def _adjust_due_date(self, key: str) -> None:
        """Adjust the due date based on key press."""
        due_input = self.query_one("#due-input", Input)
        current_value = due_input.value.strip()

        target_date = date.today()

        if current_value:
            try:
                target_date = datetime.strptime(current_value, "%Y-%m-%d").date()
            except ValueError:
                # If invalid date, stick with today as base
                pass

        delta_days = 0
        if key == "up":
            delta_days = 1
        elif key == "down":
            delta_days = -1
        elif key == "shift+up":
            delta_days = 7
        elif key == "shift+down":
            delta_days = -7

        new_date = target_date + timedelta(days=delta_days)
        due_input.value = new_date.strftime("%Y-%m-%d")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self.action_submit()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in input field."""
        # TextArea handles its own Enter key (for newlines)
        # so we only handle submission for single-line inputs here
        pass

    def action_submit(self) -> None:
        """Submit the task."""

        priority_input = self.query_one("#priority-input", Input)
        task_input = self.query_one("#task-input", TextArea)
        due_input = self.query_one("#due-input", Input)

        priority = priority_input.value.strip() or None
        # Flatten newlines to spaces for todo.txt compatibility
        task_text = task_input.text.strip().replace("\n", " ")
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
                self.app.service.update_task(
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
                new_task = self.app.service.create_task(
                    description=task_text, priority=priority, due_date=parsed_due_date
                )
                self.dismiss(
                    result={
                        "success": True,
                        "task": new_task.description,
                        "mode": "create",
                    }
                )
        except TaskValidationError as e:
            self.notify(str(e), severity="error")
            if "Priority" in str(e):
                priority_input.focus()
            elif "description" in str(e).lower():
                task_input.focus()
        except TaskOperationError as e:
            self.notify(f"Operation failed: {e}", severity="error")
        except Exception as e:
            logger.exception("Unexpected error in CreateTaskScreen")
            self.notify(f"Unexpected error: {e}", severity="error")

    def action_cancel(self) -> None:
        """Cancel the screen."""
        self.dismiss(result={"success": False, "cancelled": True})
