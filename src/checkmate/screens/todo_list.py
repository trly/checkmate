"""Main todo list screen."""

import logging
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from ..main import CheckmateApp

from textual.app import ComposeResult
from textual.command import DiscoveryHit, Hit, Hits, Provider
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header

from ..exceptions import TaskOperationError
from ..widgets.task_list import CompletedTaskList, TaskList
from .confirm import ConfirmScreen
from .create_task import CreateTaskScreen
from .filter import FilterResult, FilterScreen

logger = logging.getLogger(__name__)


class SortCommandProvider(Provider):
    """Provider for task sorting commands."""

    async def discover(self) -> Hits:
        """Discover commands to show by default."""
        screen = cast("TodoListScreen", self.screen)
        task_list = screen.task_list
        if task_list:
            yield DiscoveryHit(
                "Sort by Priority",
                lambda: task_list.apply_sort("priority"),
                help="Sort tasks by priority",
            )
            yield DiscoveryHit(
                "Sort by Context",
                lambda: task_list.apply_sort("context"),
                help="Sort tasks by context",
            )
            yield DiscoveryHit(
                "Sort by Project",
                lambda: task_list.apply_sort("project"),
                help="Sort tasks by project",
            )
            yield DiscoveryHit(
                "Sort by Due Date",
                lambda: task_list.apply_sort("due"),
                help="Sort tasks by due date",
            )
            yield DiscoveryHit(
                "Sort by Created Date",
                lambda: task_list.apply_sort("created"),
                help="Sort tasks by creation date",
            )

    async def search(self, query: str) -> Hits:
        """Search for commands."""
        matcher = self.matcher(query)
        screen = cast("TodoListScreen", self.screen)
        task_list = screen.task_list

        if not task_list:
            return

        commands = [
            (
                "Sort by Priority",
                lambda: task_list.apply_sort("priority"),
                "Sort tasks by priority",
            ),
            (
                "Sort by Context",
                lambda: task_list.apply_sort("context"),
                "Sort tasks by context",
            ),
            (
                "Sort by Project",
                lambda: task_list.apply_sort("project"),
                "Sort tasks by project",
            ),
            (
                "Sort by Due Date",
                lambda: task_list.apply_sort("due"),
                "Sort tasks by due date",
            ),
            (
                "Sort by Created Date",
                lambda: task_list.apply_sort("created"),
                "Sort tasks by creation date",
            ),
        ]

        for name, callback, help_text in commands:
            score = matcher.match(name)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(name),
                    callback,
                    help=help_text,
                )


class TodoListScreen(Screen):
    """Primary screen showing the todo and completed task lists."""

    COMMANDS: ClassVar[set] = {SortCommandProvider}

    BINDINGS: ClassVar[list] = [
        ("a", "add_todo", "Add Todo"),
        ("d", "delete_todo", "Delete Todo"),
        ("D", "force_delete_todo", "Force Delete"),
        ("e", "edit_todo", "Edit Todo"),
        ("f", "filter", "Filter"),
        ("F", "clear_filter", "Clear Filter"),
        ("C", "toggle_completed", "Toggle Completed"),
        ("j", "cursor_down", "Down"),
        ("k", "cursor_up", "Up"),
        ("1", "focus_todo", "Todo List"),
        ("2", "focus_completed", "Done List"),
    ]

    def __init__(self):
        super().__init__()
        self.task_list: TaskList | None = None
        self.completed_list: CompletedTaskList | None = None

    @property
    def app(self) -> CheckmateApp:
        return cast("CheckmateApp", super().app)

    def compose(self) -> ComposeResult:
        yield Header()
        self.task_list = TaskList(id="task-list")
        self.completed_list = CompletedTaskList(id="completed-list")
        with Vertical(id="todos-container"):
            yield self.task_list
            yield self.completed_list
        yield Footer()

    def action_cursor_down(self) -> None:
        """Move cursor down in the active list."""
        if self.task_list and self.task_list.has_focus:
            self.task_list.action_move_down()
        elif self.completed_list and self.completed_list.has_focus:
            self.completed_list.action_move_down()

    def action_cursor_up(self) -> None:
        """Move cursor up in the active list."""
        if self.task_list and self.task_list.has_focus:
            self.task_list.action_move_up()
        elif self.completed_list and self.completed_list.has_focus:
            self.completed_list.action_move_up()

    def action_add_todo(self) -> None:
        """Show the task creation modal."""

        def on_modal_result(result):
            if result and result.get("success"):
                self.app.notify(f"Task created: {result.get('task')}", timeout=2.0)
                if self.task_list:
                    self.task_list.refresh_tasks()
            elif result and result.get("error"):
                self.app.notify(
                    f"Error: {result.get('error')}", severity="error", timeout=5.0
                )

        self.app.push_screen(CreateTaskScreen(), callback=on_modal_result)

    def _delete_task(self) -> None:
        """Helper to delete the task at cursor."""
        if self.task_list and self.task_list.has_focus:
            task = self.task_list.get_task_at_cursor()
            if task:
                try:
                    self.task_list.delete_task_at_cursor()
                    self.app.notify(f"Task deleted: {task.description}", timeout=2.0)
                except TaskOperationError as e:
                    self.app.notify(
                        f"Failed to delete task: {e}", severity="error", timeout=5.0
                    )
                except Exception as e:
                    logger.exception("Unexpected error deleting task")
                    self.app.notify(
                        f"Unexpected error: {e}", severity="error", timeout=5.0
                    )
            else:
                self.app.notify("No task selected", severity="warning", timeout=2.0)
        elif self.completed_list and self.completed_list.has_focus:
            self.app.notify(
                "Deleting completed tasks is not supported",
                severity="warning",
                timeout=2.0,
            )

    def action_delete_todo(self) -> None:
        """Delete the currently selected task with confirmation."""
        if self.task_list and self.task_list.has_focus:
            task = self.task_list.get_task_at_cursor()
            if task:

                def on_confirm(result: bool | None) -> None:
                    if result:
                        self._delete_task()

                self.app.push_screen(
                    ConfirmScreen(
                        message=(
                            "Are you sure you want to delete task:\n"
                            f"'{task.description}'?"
                        )
                    ),
                    callback=on_confirm,
                )
            else:
                self.app.notify("No task selected", severity="warning", timeout=2.0)
        elif self.completed_list and self.completed_list.has_focus:
            self.app.notify(
                "Deleting completed tasks is not supported",
                severity="warning",
                timeout=2.0,
            )

    def action_force_delete_todo(self) -> None:
        """Delete the currently selected task without confirmation."""
        self._delete_task()

    def action_edit_todo(self) -> None:
        """Edit the currently selected task."""
        if self.task_list and self.task_list.has_focus:
            task = self.task_list.get_task_at_cursor()
            if task:

                def on_modal_result(result):
                    if result and result.get("success"):
                        self.app.notify(
                            f"Task updated: {result.get('task')}", timeout=2.0
                        )
                        if self.task_list:
                            self.task_list.refresh_tasks()
                    elif result and result.get("error"):
                        self.app.notify(
                            f"Error: {result.get('error')}",
                            severity="error",
                            timeout=5.0,
                        )

                self.app.push_screen(
                    CreateTaskScreen(task=task),
                    callback=on_modal_result,
                )
            else:
                self.app.notify("No task selected", severity="warning", timeout=2.0)
        elif self.completed_list and self.completed_list.has_focus:
            self.app.notify(
                "Editing completed tasks is not supported",
                severity="warning",
                timeout=2.0,
            )

    def action_focus_todo(self) -> None:
        """Focus the todo list."""
        if self.task_list:
            self.task_list.focus()

    def action_focus_completed(self) -> None:
        """Focus the completed list if visible."""
        if self.completed_list and self.completed_list.has_class("visible"):
            self.completed_list.focus()
        elif self.completed_list:
            self.app.notify("Completed list is hidden", severity="warning", timeout=2.0)

    def action_toggle_completed(self) -> None:
        """Toggle visibility of completed tasks list."""
        if self.completed_list:
            if self.completed_list.has_class("visible"):
                self.completed_list.remove_class("visible")
            else:
                self.completed_list.refresh_tasks()
                self.completed_list.add_class("visible")

    def action_filter(self) -> None:
        """Open the filter screen."""
        contexts = self.app.service.get_unique_contexts()
        projects = self.app.service.get_unique_projects()

        current_contexts: list[str] = []
        current_projects: list[str] = []
        if self.task_list:
            current_contexts = list(self.task_list.filter_contexts)
            current_projects = list(self.task_list.filter_projects)

        def on_filter_result(result: FilterResult | None) -> None:
            if result is not None and self.task_list:
                self.task_list.apply_filter(result.contexts, result.projects)

        self.app.push_screen(
            FilterScreen(
                contexts=contexts,
                projects=projects,
                selected_contexts=current_contexts,
                selected_projects=current_projects,
            ),
            callback=on_filter_result,
        )

    def action_clear_filter(self) -> None:
        """Clear any active filter."""
        if self.task_list and self.task_list.is_filtered:
            self.task_list.clear_filter()
            self.app.notify("Filter cleared", timeout=2.0)
        else:
            self.app.notify("No filter active", severity="warning", timeout=2.0)
