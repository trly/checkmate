"""Task list display widget using Textual widgets."""

import logging
import re
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from ..main import CheckmateApp

from rich.style import Style
from rich.text import Text
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Static

from ..exceptions import TaskOperationError
from ..models import Task
from ..services import TodoService

logger = logging.getLogger(__name__)


def _extract_first_context(task: Task) -> str:
    """Extract the first @context from a task description.

    Returns empty string if no context found.
    """
    # Domain Task already extracts contexts
    return task.contexts[0] if task.contexts else ""


def _extract_first_project(task: Task) -> str:
    """Extract the first +project from a task description.

    Returns empty string if no project found.
    """
    # Domain Task already extracts projects
    return task.projects[0] if task.projects else ""


def _extract_due_date(task: Task) -> str:
    """Extract due date from task attributes.

    Returns empty string if not found.
    """
    if task.due_date:
        return task.due_date.strftime("%Y-%m-%d")
    return ""


def get_active_tasks(service: TodoService):
    """Get list of active tasks from service.

    Args:
        service: TodoService instance.

    Returns:
        List of active Task objects.
    """
    return service.get_active_tasks()


def get_completed_tasks(service: TodoService):
    """Get list of completed tasks from service.

    Args:
        service: TodoService instance.

    Returns:
        List of completed Task objects.
    """
    return service.get_completed_tasks()


class TaskRow(Static):
    """
    Single task row widget displaying task information across lines
    with wrapped description.
    """

    DEFAULT_CSS = """
    TaskRow {
        height: auto;
        width: 100%;
        padding: 0;
        margin: 0;
        border: none;
    }

    TaskRow .context {
        color: $primary;
    }

    TaskRow .project {
        color: $accent;
    }
    """

    def __init__(self, task, max_width: int | None = None, **kwargs):
        super().__init__(**kwargs)
        self._todo_task = task
        self.max_width = max_width

    @property
    def task(self):
        """Get the todo task object."""
        return self._todo_task

    def _colorize_description(self, description: str) -> Text:
        """Add color styling to contexts (@word) and projects (+word) in
        description.

        Returns a Rich Text object with styles applied.
        """
        if not description:
            return Text("")

        text = Text()
        i = 0
        while i < len(description):
            # Check for @word (context)
            if description[i] == "@":
                match = re.match(r"@\w+", description[i:])
                if match:
                    word = match.group(0)
                    text.append(word, style=Style(color="cyan"))
                    i += len(word)
                    continue

            # Check for +word (project)
            if description[i] == "+":
                match = re.match(r"\+\w+", description[i:])
                if match:
                    word = match.group(0)
                    text.append(word, style=Style(color="yellow"))
                    i += len(word)
                    continue

            # Regular character
            text.append(description[i])
            i += 1

        return text

    def _extract_due_date(self) -> str:
        """Extract due date from task attributes.

        Returns:
            Due date string (YYYY-MM-DD or custom value) or empty string if
            not found.
        """
        if self._todo_task.due_date:
            return self._todo_task.due_date.strftime("%Y-%m-%d")
        return ""

    def _strip_metadata_from_description(self, description: str) -> str:
        """Remove metadata tags (due:, priority:, etc.) from description.

        Metadata is already displayed on the metadata line, so we don't want
        to show it in the description text.
        """
        if not description:
            return ""

        # Remove due:value tags (handles due:YYYY-MM-DD, due:next-week, etc.)
        description = re.sub(r"\s*due:\S+", "", description)

        # Remove other common metadata tags if present
        description = re.sub(r"\s*created:\S+", "", description)
        description = re.sub(r"\s*completed:\S+", "", description)

        return description.strip()

    def _format_row(self) -> Text:
        """Render the task row with styled description and metadata."""
        task = self._todo_task

        # Extract fields
        priority = task.priority if task.priority else ""
        created = str(task.creation_date) if task.creation_date else ""
        completed = str(task.completion_date) if task.completion_date else ""
        due = self._extract_due_date()
        description = (
            self._strip_metadata_from_description(task.description)
            if task.description
            else ""
        )

        # Build output as Rich Text
        output = Text()

        # Priority prefix
        if priority:
            output.append(f"[{priority}] ")

        # Description with styled contexts and projects
        output.append_text(self._colorize_description(description))

        # Metadata line
        metadata_parts = []
        if created:
            metadata_parts.append(Text(f"Created: {created}"))
        if due:
            if task.is_overdue:
                due_color = "red"
            elif task.is_due_today:
                due_color = "yellow"
            else:
                due_color = "green"
            due_text = Text(f"Due: {due}", style=Style(color=due_color))
            metadata_parts.append(due_text)
        if completed:
            metadata_parts.append(Text(f"Completed: {completed}"))

        if metadata_parts:
            # Build metadata line with separator between parts
            metadata = Text("\n    ")
            for i, part in enumerate(metadata_parts):
                if i > 0:
                    metadata.append(" | ")
                if isinstance(part, Text):
                    metadata.append_text(part)
                else:
                    metadata.append(str(part))
            output.append_text(metadata)

        return output

    def render(self) -> Text:
        """Render using Rich Text object."""
        return self._format_row()


class TaskList(VerticalScroll):
    """Container displaying a scrollable list of incomplete tasks.

    Supports keyboard navigation and deletion. Responds to terminal resize.
    """

    DEFAULT_CSS = """
    TaskList {
        height: 1fr;
        width: 100%;
        border: solid $primary;
        background: $surface;
    }

    TaskList > TaskRow {
        padding: 0 0 1 0;
        margin: 0;
        border-top: solid $panel;
    }

    TaskList > TaskRow.focused {
        background: $boost;
        color: $text;
    }

    TaskList > TaskRow.focused .context {
        color: $text;
    }

    TaskList > TaskRow.focused .project {
        color: $text;
    }
    """

    BINDINGS: ClassVar[list] = [
        Binding("down", "move_down", "Down", show=False),
        Binding("up", "move_up", "Up", show=False),
        Binding("delete", "delete", "Delete", show=False),
        Binding("s", "sort", "Sort"),
    ]

    tasks = reactive([])
    focused_task_index = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialized = False

    @property
    def app(self) -> "CheckmateApp":
        return cast("CheckmateApp", super().app)

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._initialized = True
        self.refresh_tasks()

    def on_resize(self, _event) -> None:
        """Handle terminal resize."""
        if self._initialized:
            self.rebuild_layout()

    def refresh_tasks(self) -> None:
        """Load tasks from file and refresh display."""
        self.tasks = get_active_tasks(self.app.service)
        self.rebuild_layout()

    def rebuild_layout(self) -> None:
        """Rebuild task rows with current width."""
        # Clear existing rows
        rows = self.query(TaskRow)
        if rows:
            rows.remove()

        # Calculate width (use current width or fallback)
        width = self.size.width if self.size.width > 0 else 80

        # Add task rows
        for task in self.tasks:
            row = TaskRow(task, max_width=width)
            self.mount(row)

        # Update focus styling
        self._update_focus_styling()

    def _update_focus_styling(self) -> None:
        """Update CSS class for focused row."""
        rows = self.query(TaskRow)
        for i, row in enumerate(rows):
            if i == self.focused_task_index:
                row.add_class("focused")
            else:
                row.remove_class("focused")

    def watch_focused_task_index(self, _index: int) -> None:
        """Update focus styling when index changes."""
        self._update_focus_styling()

    def get_task_at_cursor(self):
        """Get the Task object at the current cursor position.

        Returns:
            Task object if cursor is on a valid row, None otherwise.
        """
        if 0 <= self.focused_task_index < len(self.tasks):
            return self.tasks[self.focused_task_index]
        return None

    def delete_task_at_cursor(self) -> None:
        """Delete the task at the current cursor position.

        Raises:
            TaskOperationError: If deletion fails.
        """
        task = self.get_task_at_cursor()
        if not task:
            return

        self.app.service.delete_task(task)
        self.refresh_tasks()

    def move_focus_down(self) -> None:
        """Move focus to next task."""
        if self.focused_task_index < len(self.tasks) - 1:
            self.focused_task_index += 1

    def move_focus_up(self) -> None:
        """Move focus to previous task."""
        if self.focused_task_index > 0:
            self.focused_task_index -= 1

    def action_move_down(self) -> None:
        """Action handler for down key."""
        self.move_focus_down()

    def action_move_up(self) -> None:
        """Action handler for up key."""
        self.move_focus_up()

    def action_delete(self) -> None:
        """Action handler for delete key."""
        try:
            self.delete_task_at_cursor()
        except TaskOperationError as e:
            self.app.notify(f"Failed to delete task: {e}", severity="error")
        except Exception as e:
            logger.exception("Unexpected error deleting task")
            self.app.notify(f"Unexpected error: {e}", severity="error")

    def action_sort(self) -> None:
        """Action handler for sort key - opens sort selection screen."""
        from ..screens.sort_select import SortSelectScreen

        def on_sort_selected(attribute: str) -> None:
            """Apply the selected sort."""
            self.apply_sort(attribute)

        self.app.push_screen(SortSelectScreen(callback=on_sort_selected))

    def apply_sort(self, attribute: str) -> None:
        """Apply sorting to tasks by the specified attribute.

        Args:
            attribute: One of 'priority', 'context', 'project', 'due',
                'created'
        """
        if attribute == "priority":
            self.tasks = sorted(
                self.tasks, key=lambda t: (t.priority is None, t.priority or "")
            )
        elif attribute == "context":
            self.tasks = sorted(
                self.tasks,
                key=lambda t: (
                    _extract_first_context(t) == "",
                    _extract_first_context(t),
                ),
            )
        elif attribute == "project":
            self.tasks = sorted(
                self.tasks,
                key=lambda t: (
                    _extract_first_project(t) == "",
                    _extract_first_project(t),
                ),
            )
        elif attribute == "due":
            self.tasks = sorted(
                self.tasks,
                key=lambda t: (_extract_due_date(t) == "", _extract_due_date(t)),
            )
        elif attribute == "created":
            self.tasks = sorted(
                self.tasks,
                key=lambda t: (
                    t.creation_date is None,
                    str(t.creation_date) if t.creation_date else "",
                ),
            )

        # Rebuild layout to show sorted tasks
        self.rebuild_layout()


class CompletedTaskList(VerticalScroll):
    """Container displaying a scrollable list of completed tasks from done.txt.

    Similar to TaskList but read-only, displays only completed tasks.
    """

    DEFAULT_CSS = """
    CompletedTaskList {
        height: 1fr;
        width: 100%;
        border: solid $panel;
        background: $surface;
        display: none;
    }

    CompletedTaskList.visible {
        display: block;
    }

    CompletedTaskList > TaskRow {
        padding: 0 0 1 0;
        margin: 0;
        border-top: solid $panel;
    }

    CompletedTaskList > TaskRow.focused {
        background: $boost;
        color: $text;
    }

    CompletedTaskList > TaskRow.focused .context {
        color: $text;
    }

    CompletedTaskList > TaskRow.focused .project {
        color: $text;
    }
    """

    BINDINGS: ClassVar[list] = [
        Binding("down", "move_down", "Down", show=False),
        Binding("up", "move_up", "Up", show=False),
    ]

    tasks = reactive([])
    focused_task_index = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialized = False

    @property
    def app(self) -> "CheckmateApp":
        return cast("CheckmateApp", super().app)

    def on_mount(self) -> None:
        """Initialize on mount."""
        self._initialized = True
        self.refresh_tasks()

    def on_resize(self, _event) -> None:
        """Handle terminal resize."""
        if self._initialized:
            self.rebuild_layout()

    def refresh_tasks(self) -> None:
        """Load tasks from file and refresh display."""
        self.tasks = get_completed_tasks(self.app.service)
        self.rebuild_layout()

    def rebuild_layout(self) -> None:
        """Rebuild task rows with current width."""
        # Clear existing rows
        rows = self.query(TaskRow)
        if rows:
            rows.remove()

        # Calculate width (use current width or fallback)
        width = self.size.width if self.size.width > 0 else 80

        # Add task rows
        for task in self.tasks:
            row = TaskRow(task, max_width=width)
            self.mount(row)

        # Update focus styling
        self._update_focus_styling()

    def _update_focus_styling(self) -> None:
        """Update CSS class for focused row."""
        rows = self.query(TaskRow)
        for i, row in enumerate(rows):
            if i == self.focused_task_index:
                row.add_class("focused")
            else:
                row.remove_class("focused")

    def watch_focused_task_index(self, _index: int) -> None:
        """Update focus styling when index changes."""
        self._update_focus_styling()

    def get_task_at_cursor(self):
        """Get the Task object at the current cursor position.

        Returns:
            Task object if cursor is on a valid row, None otherwise.
        """
        if 0 <= self.focused_task_index < len(self.tasks):
            return self.tasks[self.focused_task_index]
        return None

    def move_focus_down(self) -> None:
        """Move focus to next task."""
        if self.focused_task_index < len(self.tasks) - 1:
            self.focused_task_index += 1

    def move_focus_up(self) -> None:
        """Move focus to previous task."""
        if self.focused_task_index > 0:
            self.focused_task_index -= 1

    def action_move_down(self) -> None:
        """Action handler for down key."""
        self.move_focus_down()

    def action_move_up(self) -> None:
        """Action handler for up key."""
        self.move_focus_up()
