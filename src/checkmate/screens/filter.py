"""Filter modal screen for selecting contexts and projects."""

from dataclasses import dataclass
from typing import ClassVar

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, SelectionList
from textual.widgets.selection_list import Selection


@dataclass
class FilterResult:
    """Result returned when filter is applied."""

    contexts: list[str]
    projects: list[str]


class FilterScreen(ModalScreen[FilterResult | None]):
    """Modal screen for filtering by contexts and projects."""

    BINDINGS: ClassVar[list] = [
        ("escape", "cancel", "Cancel"),
        ("enter", "apply", "Apply"),
    ]

    def __init__(
        self,
        contexts: list[str],
        projects: list[str],
        selected_contexts: list[str] | None = None,
        selected_projects: list[str] | None = None,
    ):
        super().__init__()
        self._contexts = contexts
        self._projects = projects
        self._selected_contexts = set(selected_contexts or [])
        self._selected_projects = set(selected_projects or [])

    def compose(self) -> ComposeResult:
        with Container():
            yield Label("Filter Tasks", id="title")

            with Vertical():
                yield Label("Contexts", classes="list-label")
                context_selections = [
                    Selection(
                        f"@{ctx}",
                        ctx,
                        initial_state=(ctx in self._selected_contexts),
                    )
                    for ctx in self._contexts
                ]
                yield SelectionList[str](*context_selections, id="contexts-list")

                yield Label("Projects", classes="list-label")
                project_selections = [
                    Selection(
                        f"+{proj}",
                        proj,
                        initial_state=(proj in self._selected_projects),
                    )
                    for proj in self._projects
                ]
                yield SelectionList[str](*project_selections, id="projects-list")

            with Horizontal():
                yield Button("Apply", variant="primary", id="apply-btn")
                yield Button("Clear", id="clear-btn")
                yield Button("Cancel", variant="error", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply-btn":
            self._apply_filter()
        elif event.button.id == "clear-btn":
            self._clear_selections()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def action_apply(self) -> None:
        self._apply_filter()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _apply_filter(self) -> None:
        contexts_list = self.query_one("#contexts-list", SelectionList)
        projects_list = self.query_one("#projects-list", SelectionList)

        result = FilterResult(
            contexts=list(contexts_list.selected),
            projects=list(projects_list.selected),
        )
        self.dismiss(result)

    def _clear_selections(self) -> None:
        contexts_list = self.query_one("#contexts-list", SelectionList)
        projects_list = self.query_one("#projects-list", SelectionList)

        contexts_list.deselect_all()
        projects_list.deselect_all()
