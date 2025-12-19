"""Task list display widget using Textual widgets."""

import logging
import re
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from ..main import CheckmateApp

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
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

    TaskRow .description-line {
        width: 100%;
        height: auto;
    }

    TaskRow .description-segment {
        width: auto;
        height: auto;
    }

    TaskRow .context {
        color: $secondary;
    }

    TaskRow .project {
        color: $warning;
    }

    TaskRow .metadata-line {
        width: 100%;
        height: auto;
        padding-left: 4;
    }

    TaskRow .metadata-segment {
        width: auto;
        height: auto;
    }

    TaskRow .due-overdue {
        color: $error;
    }

    TaskRow .due-today {
        color: $warning;
    }

    TaskRow .due-future {
        color: $success;
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

    def _extract_due_date(self) -> str:
        """Extract due date from task attributes."""
        if self._todo_task.due_date:
            return self._todo_task.due_date.strftime("%Y-%m-%d")
        return ""

    def _strip_metadata_from_description(self, description: str) -> str:
        """Remove metadata tags (due:, priority:, etc.) from description."""
        if not description:
            return ""

        description = re.sub(r"\s*due:\S+", "", description)
        description = re.sub(r"\s*created:\S+", "", description)
        description = re.sub(r"\s*completed:\S+", "", description)

        return description.strip()

    def _parse_description(self, description: str):
        """Parse description into segments with CSS classes.

        Yields tuples of (text, css_class) where css_class may be None.
        """
        if not description:
            return

        i = 0
        current_text = ""

        while i < len(description):
            if description[i] == "@":
                match = re.match(r"@\w+", description[i:])
                if match:
                    if current_text:
                        yield (current_text, None)
                        current_text = ""
                    yield (match.group(0), "context")
                    i += len(match.group(0))
                    continue

            if description[i] == "+":
                match = re.match(r"\+\w+", description[i:])
                if match:
                    if current_text:
                        yield (current_text, None)
                        current_text = ""
                    yield (match.group(0), "project")
                    i += len(match.group(0))
                    continue

            current_text += description[i]
            i += 1

        if current_text:
            yield (current_text, None)

    def compose(self) -> ComposeResult:
        """Compose the task row with styled widgets."""
        task = self._todo_task

        priority = task.priority if task.priority else ""
        created = str(task.creation_date) if task.creation_date else ""
        completed = str(task.completion_date) if task.completion_date else ""
        due = self._extract_due_date()
        description = (
            self._strip_metadata_from_description(task.description)
            if task.description
            else ""
        )

        with Vertical():
            with Horizontal(classes="description-line"):
                if priority:
                    yield Static(f"[{priority}] ", classes="description-segment")

                for text, css_class in self._parse_description(description):
                    classes = "description-segment"
                    if css_class:
                        classes += f" {css_class}"
                    yield Static(text, classes=classes)

            metadata_parts = []
            if created:
                metadata_parts.append(("Created: " + created, None))
            if due:
                if task.is_overdue:
                    due_class = "due-overdue"
                elif task.is_due_today:
                    due_class = "due-today"
                else:
                    due_class = "due-future"
                metadata_parts.append(("Due: " + due, due_class))
            if completed:
                metadata_parts.append(("Completed: " + completed, None))

            if metadata_parts:
                with Horizontal(classes="metadata-line"):
                    for i, (text, css_class) in enumerate(metadata_parts):
                        if i > 0:
                            yield Static(" | ", classes="metadata-segment")
                        classes = "metadata-segment"
                        if css_class:
                            classes += f" {css_class}"
                        yield Static(text, classes=classes)


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

    TaskList:focus {
        border: solid $accent;
    }

    TaskList.filtered {
        border: solid $warning;
    }

    TaskList.filtered:focus {
        border: solid $warning-lighten-2;
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
        Binding("x", "complete_todo", "Complete Todo"),
    ]

    tasks = reactive([])
    focused_task_index = reactive(0)
    can_focus = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialized = False
        self._filter_contexts: set[str] = set()
        self._filter_projects: set[str] = set()

    @property
    def filter_contexts(self) -> set[str]:
        """Get the current context filter."""
        return self._filter_contexts

    @property
    def filter_projects(self) -> set[str]:
        """Get the current project filter."""
        return self._filter_projects

    @property
    def is_filtered(self) -> bool:
        """Return True if any filter is active."""
        return bool(self._filter_contexts or self._filter_projects)

    def apply_filter(self, contexts: list[str], projects: list[str]) -> None:
        """Apply filter by contexts and/or projects.

        Args:
            contexts: List of context names to filter by (OR logic).
            projects: List of project names to filter by (OR logic).
        """
        self._filter_contexts = set(contexts)
        self._filter_projects = set(projects)
        self._update_filtered_class()
        if self._initialized:
            self.rebuild_layout()

    def clear_filter(self) -> None:
        """Clear all filters."""
        self._filter_contexts = set()
        self._filter_projects = set()
        self._update_filtered_class()
        if self._initialized:
            self.rebuild_layout()

    def _update_filtered_class(self) -> None:
        """Update the 'filtered' CSS class based on filter state."""
        if self.is_filtered:
            self.add_class("filtered")
        else:
            self.remove_class("filtered")

    def _task_matches_filter(self, task: Task) -> bool:
        """Check if a task matches the current filter.

        Returns True if:
        - No filter is active (both sets empty)
        - Task has ANY matching context OR ANY matching project
        """
        if not self.is_filtered:
            return True

        # Check if task has any matching context
        if self._filter_contexts:
            task_contexts = set(task.contexts)
            if task_contexts & self._filter_contexts:
                return True

        # Check if task has any matching project
        if self._filter_projects:
            task_projects = set(task.projects)
            if task_projects & self._filter_projects:
                return True

        # If filter is active but no match found
        return False

    @property
    def app(self) -> CheckmateApp:
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
        """Rebuild task rows with current width, applying any active filter."""
        # Clear existing rows
        rows = self.query(TaskRow)
        if rows:
            rows.remove()

        # Calculate width (use current width or fallback)
        width = self.size.width if self.size.width > 0 else 80

        # Add task rows (filtered)
        for task in self.tasks:
            if self._task_matches_filter(task):
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

    def action_complete_todo(self) -> None:
        """Action handler for complete todo key."""
        task = self.get_task_at_cursor()
        if task:
            try:
                self.app.service.complete_task(task)
                self.app.notify(f"Task completed: {task.description}", timeout=2.0)
                self.refresh_tasks()
                # Refresh completed list
                try:
                    completed_list = cast(
                        "CompletedTaskList", self.screen.query_one("#completed-list")
                    )
                    completed_list.refresh_tasks()
                except Exception:
                    pass
            except TaskOperationError as e:
                self.app.notify(
                    f"Failed to complete task: {e}", severity="error", timeout=5.0
                )
            except Exception as e:
                logger.exception("Unexpected error completing task")
                self.app.notify(f"Unexpected error: {e}", severity="error", timeout=5.0)
        else:
            self.app.notify("No task selected", severity="warning", timeout=2.0)

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

    CompletedTaskList:focus {
        border: solid $accent;
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
        Binding("r", "reopen_todo", "Reopen Todo"),
    ]

    def action_reopen_todo(self) -> None:
        """Action handler for reopen todo key."""
        task = self.get_task_at_cursor()
        if task:
            try:
                self.app.service.reopen_task(task)
                self.app.notify(f"Task reopened: {task.description}", timeout=2.0)
                self.refresh_tasks()
                # Refresh active list
                try:
                    task_list = cast("TaskList", self.screen.query_one("#task-list"))
                    task_list.refresh_tasks()
                except Exception:
                    pass
            except TaskOperationError as e:
                self.app.notify(
                    f"Failed to reopen task: {e}", severity="error", timeout=5.0
                )
            except Exception as e:
                logger.exception("Unexpected error reopening task")
                self.app.notify(f"Unexpected error: {e}", severity="error", timeout=5.0)
        else:
            self.app.notify("No task selected", severity="warning", timeout=2.0)

    tasks = reactive([])
    focused_task_index = reactive(0)
    can_focus = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._initialized = False

    @property
    def app(self) -> CheckmateApp:
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
