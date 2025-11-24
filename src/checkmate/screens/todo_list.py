"""Main todo list screen."""

import logging
from typing import TYPE_CHECKING, ClassVar, cast

if TYPE_CHECKING:
    from ..main import CheckmateApp

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header

from ..exceptions import TaskOperationError
from ..widgets.task_list import CompletedTaskList, TaskList
from .create_task import CreateTaskScreen

logger = logging.getLogger(__name__)


class TodoListScreen(Screen):
    """Primary screen showing the todo and completed task lists."""

    BINDINGS: ClassVar[list] = [
        ("a", "add_todo", "Add Todo"),
        ("d", "delete_todo", "Delete Todo"),
        ("e", "edit_todo", "Edit Todo"),
        ("x", "complete_todo", "Complete Todo"),
        ("shift+c", "toggle_completed", "Toggle Completed"),
    ]

    def __init__(self):
        super().__init__()
        self.task_list: TaskList | None = None
        self.completed_list: CompletedTaskList | None = None

    @property
    def app(self) -> "CheckmateApp":
        return cast("CheckmateApp", super().app)

    def compose(self) -> ComposeResult:
        yield Header()
        self.task_list = TaskList(id="task-list")
        self.completed_list = CompletedTaskList(
            id="completed-list"
        )
        with Vertical(id="todos-container"):
            yield self.task_list
            yield self.completed_list
        yield Footer()

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

        self.app.push_screen(
            CreateTaskScreen(), callback=on_modal_result
        )

    def action_delete_todo(self) -> None:
        """Delete the currently selected task."""
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

    def action_complete_todo(self) -> None:
        """Mark the currently selected task as completed."""
        if self.task_list and self.task_list.has_focus:
            task = self.task_list.get_task_at_cursor()
            if task:
                try:
                    self.app.service.complete_task(task)
                    self.app.notify(f"Task completed: {task.description}", timeout=2.0)
                    if self.task_list:
                        self.task_list.refresh_tasks()
                    if self.completed_list:
                        self.completed_list.refresh_tasks()
                except TaskOperationError as e:
                    self.app.notify(
                        f"Failed to complete task: {e}", severity="error", timeout=5.0
                    )
                except Exception as e:
                    logger.exception("Unexpected error completing task")
                    self.app.notify(
                        f"Unexpected error: {e}", severity="error", timeout=5.0
                    )
            else:
                self.app.notify("No task selected", severity="warning", timeout=2.0)

    def action_toggle_completed(self) -> None:
        """Toggle visibility of completed tasks list."""
        if self.completed_list:
            if self.completed_list.has_class("visible"):
                self.completed_list.remove_class("visible")
            else:
                self.completed_list.refresh_tasks()
                self.completed_list.add_class("visible")
