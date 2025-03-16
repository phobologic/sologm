"""
Command context implementations.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class CLIContext:
    """CLI-specific command context."""
    working_directory: str
    user: str
    extra_args: Dict[str, Any] = field(default_factory=dict)

    @property
    def workspace_id(self) -> str:
        """Get workspace ID from working directory."""
        return f"cli:{self.working_directory}"

    @property
    def formatted_user_id(self) -> str:
        """Get user ID."""
        return f"cli:{self.user}"

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get CLI-specific metadata."""
        return self.extra_args

@dataclass
class SlackContext:
    """Slack-specific command context."""
    channel_id: str
    team_id: str
    user_id: str
    response_url: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def workspace_id(self) -> str:
        """Get workspace ID from Slack channel."""
        return f"slack:{self.team_id}:{self.channel_id}"

    @property
    def formatted_user_id(self) -> str:
        """Get user ID from Slack."""
        return f"slack:{self.user_id}"

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get Slack-specific metadata."""
        data = self.extra_data.copy()
        if self.response_url:
            data["response_url"] = self.response_url
        return data 