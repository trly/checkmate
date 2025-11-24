class CheckmateError(Exception):
    """Base exception for all Checkmate errors."""

    pass


class TaskValidationError(CheckmateError):
    """Raised when task data is invalid."""

    pass


class TaskOperationError(CheckmateError):
    """Raised when a task operation fails (persistence, etc.)."""

    pass
