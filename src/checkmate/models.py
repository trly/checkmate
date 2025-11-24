import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional


@dataclass
class Task:
    description: str
    is_completed: bool = False
    priority: Optional[str] = None
    creation_date: Optional[date] = None
    completion_date: Optional[date] = None
    projects: List[str] = field(default_factory=list)
    contexts: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Parse projects and contexts from description if not provided."""
        if not self.projects:
            self.projects = re.findall(r"\+(\w+)", self.description)
        if not self.contexts:
            self.contexts = re.findall(r"@(\w+)", self.description)

    @property
    def id(self) -> Optional[str]:
        """Get the stable task ID."""
        val = self.attributes.get("cmid")
        if isinstance(val, list):
            return val[0] if val else None
        return val

    @property
    def due_date(self) -> Optional[date]:
        """Get due date from attributes if present."""
        due_str = self.attributes.get("due")
        if not due_str:
            return None

        if isinstance(due_str, list):
            due_str = due_str[0]

        try:
            return datetime.strptime(due_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

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
