"""
Command execution results.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    data: Any
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None

    @property
    def is_error(self) -> bool:
        """Check if this result represents an error."""
        return not self.success

    def format_for_cli(self) -> str:
        """Format the result for CLI output."""
        if self.is_error:
            return f"Error: {self.message}"
        return self.message

    def format_for_slack(self) -> Dict[str, Any]:
        """Format the result for Slack output."""
        if self.is_error:
            return {
                "response_type": "ephemeral",
                "text": f"Error: {self.message}"
            }
        return {
            "response_type": "in_channel",
            "text": self.message
        } 