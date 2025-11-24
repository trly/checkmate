import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

# Type alias for attributes
Attributes = Dict[str, Union[str, List[str]]]


@dataclass
class Task:
    description: str
    is_completed: bool = False
    priority: Optional[str] = None
    creation_date: Optional[date] = None
    completion_date: Optional[date] = None
    projects: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)
    attributes: Attributes = field(default_factory=dict)

    def __post_init__(self):
        """Parse projects and contexts from description if not provided."""
        if not self.projects and not self.contexts:
             self.refresh_metadata()

    def refresh_metadata(self):
        """Parse projects and contexts from description."""
        # Using \S to match any non-whitespace character, consistent with todo.txt spec
        self.projects = re.findall(r"\+(\S+)", self.description)
        self.contexts = re.findall(r"@(\S+)", self.description)

    @property
    def id(self) -> Optional[str]:
        """Get the stable task ID."""
        val = self.attributes.get("cmid")
        if isinstance(val, list):
            return val[0] if val else None
        return val  # type: ignore

    @property
    def due_date(self) -> Optional[date]:
        """Get due date from attributes if present."""
        due_str = self.attributes.get("due")
        if not due_str:
            return None

        if isinstance(due_str, list):
            due_str = due_str[0]

        try:
            return datetime.strptime(str(due_str), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    @due_date.setter
    def due_date(self, value: Optional[date]):
        """Set due date in attributes."""
        if value is None:
            if "due" in self.attributes:
                del self.attributes["due"]
        else:
            self.attributes["due"] = value.strftime("%Y-%m-%d")

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if self.is_completed or not self.due_date:
            return False
        return self.due_date < datetime.now().date()

    @property
    def is_due_today(self) -> bool:
        """Check if task is due today."""
        if self.is_completed or not self.due_date:
            return False
        return self.due_date == datetime.now().date()

    def complete(self):
        """Mark task as completed."""
        self.is_completed = True
        self.completion_date = date.today()

    def reopen(self):
        """Mark task as incomplete."""
        self.is_completed = False
        self.completion_date = None
