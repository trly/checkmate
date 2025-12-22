"""Tests for dynamic action visibility via check_action."""

import pytest

from checkmate.main import CheckmateApp
from checkmate.repository import FileTaskRepository
from checkmate.screens.todo_list import TodoListScreen
from checkmate.services import TodoService


@pytest.fixture
def app_with_tasks(tmp_path):
    """Create an app with some test tasks."""
    todo_file = tmp_path / "todo.txt"
    todo_file.write_text(
        "Task 1\n" "Task 2 +project @context\n" "(A) Task 3 due:2025-01-01\n"
    )
    done_file = tmp_path / "done.txt"
    done_file.write_text("x 2025-01-01 Task 1 (completed)\n")

    repository = FileTaskRepository(todo_file=str(todo_file), done_file=str(done_file))
    service = TodoService(repository)
    return CheckmateApp(service=service)


@pytest.fixture
def app_empty(tmp_path):
    """Create an app with no tasks."""
    todo_file = tmp_path / "todo.txt"
    todo_file.write_text("")
    done_file = tmp_path / "done.txt"
    done_file.write_text("")

    repository = FileTaskRepository(todo_file=str(todo_file), done_file=str(done_file))
    service = TodoService(repository)
    return CheckmateApp(service=service)


class TestTodoListScreenCheckAction:
    """Tests for TodoListScreen.check_action."""

    @pytest.mark.asyncio
    async def test_delete_action_available_when_task_selected(self, app_with_tasks):
        """Delete action should be available when task is selected."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            # Make sure task list has focus and a task is selected
            task_list.focus()
            result = screen.check_action("delete_todo", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_action_hidden_when_no_task_selected(self, app_empty):
        """Delete action should be hidden when no task selected."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = screen.check_action("delete_todo", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_force_delete_action_available_when_task_selected(
        self, app_with_tasks
    ):
        """Force delete action should be available when task is selected."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = screen.check_action("force_delete_todo", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_force_delete_action_hidden_when_no_task(self, app_empty):
        """Force delete action should be hidden when no task."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = screen.check_action("force_delete_todo", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_edit_action_available_when_task_selected(self, app_with_tasks):
        """Edit action should be available when task is selected."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = screen.check_action("edit_todo", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_edit_action_hidden_when_no_task(self, app_empty):
        """Edit action should be hidden when no task."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = screen.check_action("edit_todo", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_complete_action_available_when_task_selected(self, app_with_tasks):
        """Complete action should be available when task is selected."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = screen.check_action("complete_todo", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_complete_action_hidden_when_no_task(self, app_empty):
        """Complete action should be hidden when no task."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = screen.check_action("complete_todo", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_filter_action_available_when_tasks_exist(self, app_with_tasks):
        """Filter action should be available when tasks exist."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)

            result = screen.check_action("filter", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_filter_action_hidden_when_no_tasks(self, app_empty):
        """Filter action should be hidden when no tasks."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)

            result = screen.check_action("filter", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_clear_filter_action_hidden_initially(self, app_with_tasks):
        """Clear filter action should be hidden when no filter is active."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            # No filter initially
            assert not task_list.is_filtered
            result = screen.check_action("clear_filter", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_clear_filter_action_available_when_filtered(self, app_with_tasks):
        """Clear filter action should be available when filter is active."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            # Apply a filter
            task_list.apply_filter(["context"], [])
            assert task_list.is_filtered

            result = screen.check_action("clear_filter", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_reopen_action_hidden_when_no_completed_list(self, app_with_tasks):
        """Reopen action should be hidden when completed list not visible."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            completed_list = screen.completed_list
            assert completed_list is not None

            # Completed list not visible initially
            assert not completed_list.has_class("visible")
            result = screen.check_action("reopen_todo", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_reopen_action_hidden_when_completed_not_focused(
        self, app_with_tasks
    ):
        """Reopen action should be hidden when completed list not focused."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            completed_list = screen.completed_list
            assert task_list is not None
            assert completed_list is not None

            # Make completed list visible but don't focus it
            completed_list.add_class("visible")
            task_list.focus()

            result = screen.check_action("reopen_todo", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_always_show_actions(self, app_empty):
        """Always-shown actions should always be available."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)

            # These actions should always be available
            assert screen.check_action("add_todo", ()) is True
            assert screen.check_action("toggle_completed", ()) is True
            assert screen.check_action("cursor_up", ()) is True
            assert screen.check_action("cursor_down", ()) is True
            assert screen.check_action("focus_todo", ()) is True
            assert screen.check_action("focus_completed", ()) is True


class TestTaskListCheckAction:
    """Tests for TaskList.check_action."""

    @pytest.mark.asyncio
    async def test_sort_action_available_when_tasks_exist(self, app_with_tasks):
        """Sort action should be available when tasks exist."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = task_list.check_action("sort", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_sort_action_hidden_when_no_tasks(self, app_empty):
        """Sort action should be hidden when no tasks."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = task_list.check_action("sort", ())
            assert result is False

    @pytest.mark.asyncio
    async def test_complete_todo_action_available_when_task_selected(
        self, app_with_tasks
    ):
        """Complete todo action should be available when task selected."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = task_list.check_action("complete_todo", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_complete_todo_action_hidden_when_no_task(self, app_empty):
        """Complete todo action should be hidden when no task."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)
            task_list = screen.task_list
            assert task_list is not None

            task_list.focus()
            result = task_list.check_action("complete_todo", ())
            assert result is False


class TestCompletedTaskListCheckAction:
    """Tests for CompletedTaskList.check_action."""

    @pytest.mark.asyncio
    async def test_reopen_action_available_when_task_selected(self, app_with_tasks):
        """Reopen action should be available when task selected."""
        async with app_with_tasks.run_test():
            screen = app_with_tasks.screen
            assert isinstance(screen, TodoListScreen)
            completed_list = screen.completed_list
            assert completed_list is not None

            # Make it visible
            completed_list.add_class("visible")

            # Should be available when a completed task is selected
            # (there is one in our fixture)
            assert len(completed_list.tasks) > 0
            result = completed_list.check_action("reopen_todo", ())
            assert result is True

    @pytest.mark.asyncio
    async def test_reopen_action_hidden_when_no_completed_tasks(self, app_empty):
        """Reopen action should be hidden when no completed tasks."""
        async with app_empty.run_test():
            screen = app_empty.screen
            assert isinstance(screen, TodoListScreen)
            completed_list = screen.completed_list
            assert completed_list is not None

            completed_list.add_class("visible")
            result = completed_list.check_action("reopen_todo", ())
            assert result is False
