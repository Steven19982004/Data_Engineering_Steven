class PipelineError(Exception):
    """Raised when a pipeline stage fails."""


class DataValidationError(Exception):
    """Raised when raw/processed data fails validation."""


class AgentUnavailableError(Exception):
    """Raised when the requested agent mode cannot be started."""


class ToolExecutionError(Exception):
    """Raised when a tool invocation fails."""
