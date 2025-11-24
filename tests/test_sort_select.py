"""Tests for the sort selection modal screen."""

import pytest
from textual.app import App, ComposeResult
from textual.widgets import Button

from checkmate.screens.sort_select import SortSelectScreen


@pytest.mark.asyncio
async def test_sort_select_screen_compose():
    """Test that SortSelectScreen composes with all button options."""

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield SortSelectScreen(callback=lambda x: None)

    app = TestApp()
    async with app.run_test() as _:
        app.query_one(SortSelectScreen)

        # Query buttons by their IDs
        buttons = app.query("Button")
        button_ids = [b.id for b in buttons]

        assert "sort-priority-btn" in button_ids
        assert "sort-context-btn" in button_ids
        assert "sort-project-btn" in button_ids
        assert "sort-due-btn" in button_ids
        assert "sort-created-btn" in button_ids


@pytest.mark.asyncio
async def test_sort_select_priority_button():
    """Test clicking the Priority sort button."""
    callback_results = []

    def test_callback(attr):
        callback_results.append(attr)

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield SortSelectScreen(callback=test_callback)

    app = TestApp()
    async with app.run_test() as pilot:
        button = app.query_one("#sort-priority-btn", Button)
        button.press()
        await pilot.pause()

        assert "priority" in callback_results


@pytest.mark.asyncio
async def test_sort_select_context_button():
    """Test clicking the Context sort button."""
    callback_results = []

    def test_callback(attr):
        callback_results.append(attr)

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield SortSelectScreen(callback=test_callback)

    app = TestApp()
    async with app.run_test() as pilot:
        button = app.query_one("#sort-context-btn", Button)
        button.press()
        await pilot.pause()

        assert "context" in callback_results


@pytest.mark.asyncio
async def test_sort_select_project_button():
    """Test clicking the Project sort button."""
    callback_results = []

    def test_callback(attr):
        callback_results.append(attr)

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield SortSelectScreen(callback=test_callback)

    app = TestApp()
    async with app.run_test() as pilot:
        button = app.query_one("#sort-project-btn", Button)
        button.press()
        await pilot.pause()

        assert "project" in callback_results


@pytest.mark.asyncio
async def test_sort_select_due_button():
    """Test clicking the Due date sort button."""
    callback_results = []

    def test_callback(attr):
        callback_results.append(attr)

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield SortSelectScreen(callback=test_callback)

    app = TestApp()
    async with app.run_test() as pilot:
        button = app.query_one("#sort-due-btn", Button)
        button.press()
        await pilot.pause()

        assert "due" in callback_results


@pytest.mark.asyncio
async def test_sort_select_created_button():
    """Test clicking the Created date sort button."""
    callback_results = []

    def test_callback(attr):
        callback_results.append(attr)

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield SortSelectScreen(callback=test_callback)

    app = TestApp()
    async with app.run_test() as pilot:
        button = app.query_one("#sort-created-btn", Button)
        button.press()
        await pilot.pause()

        assert "created" in callback_results


@pytest.mark.asyncio
async def test_sort_select_escape_closes():
    """Test that Escape key closes the screen without callback."""
    callback_called = False

    def test_callback(attr):
        nonlocal callback_called
        callback_called = True

    class TestApp(App):
        def compose(self) -> ComposeResult:
            yield SortSelectScreen(callback=test_callback)

    app = TestApp()
    async with app.run_test() as pilot:
        app.query_one(SortSelectScreen)

        # Press escape
        await pilot.press("escape")
        await pilot.pause()

        # Callback should not have been called
        assert not callback_called
