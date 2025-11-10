"""
CLI Logger - Centralized logging for Socrates CLI actions

Tracks user actions, commands, authentication, project/session operations,
and errors for monitoring and debugging purposes.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class CLILogger:
    """Manages CLI action logging to file"""

    def __init__(self, enabled: bool = False):
        """
        Initialize CLI logger.

        Args:
            enabled: Whether logging is enabled by default
        """
        self.enabled = enabled
        self.log_dir = Path.home() / ".socrates" / "logs"
        self.log_file = self.log_dir / "cli.log"

        # Create log directory if needed
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup Python logging
        self.logger = logging.getLogger("socrates_cli")
        self.logger.setLevel(logging.DEBUG)

        # File handler
        handler = logging.FileHandler(self.log_file, encoding='utf-8')
        handler.setLevel(logging.DEBUG)

        # Formatter: [TIMESTAMP] [CATEGORY] [ACTION] [DETAILS]
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def set_enabled(self, enabled: bool):
        """Enable or disable logging"""
        self.enabled = enabled

    def is_enabled(self) -> bool:
        """Check if logging is enabled"""
        return self.enabled

    def _log(self, category: str, action: str, details: Optional[Dict[str, Any]] = None):
        """Internal logging method"""
        if not self.enabled:
            return

        # Format message
        message = f"{category}: {action}"
        if details:
            detail_parts = [f"{k}={v}" for k, v in details.items()]
            message += f" | {', '.join(detail_parts)}"

        self.logger.info(message)

    # Authentication logging
    def log_login(self, username: str, email: str):
        """Log user login"""
        self._log("AUTH", "User login", {"username": username, "email": email})

    def log_logout(self, email: str):
        """Log user logout"""
        self._log("AUTH", "User logout", {"email": email})

    def log_register(self, username: str, email: str):
        """Log user registration"""
        self._log("AUTH", "User registration", {"username": username, "email": email})

    # Project logging
    def log_project_create(self, name: str, project_id: str):
        """Log project creation"""
        self._log("PROJECT", "Project created", {"name": name, "project_id": project_id})

    def log_project_select(self, name: str, project_id: str):
        """Log project selection"""
        self._log("PROJECT", "Project selected", {"name": name, "project_id": project_id})

    def log_project_delete(self, name: str, project_id: str):
        """Log project deletion"""
        self._log("PROJECT", "Project deleted", {"name": name, "project_id": project_id})

    # Session logging
    def log_session_start(self, session_id: str, mode: str, project_id: str):
        """Log session start"""
        self._log("SESSION", "Session started", {
            "session_id": session_id,
            "mode": mode,
            "project_id": project_id
        })

    def log_session_end(self, session_id: str):
        """Log session end"""
        self._log("SESSION", "Session ended", {"session_id": session_id})

    def log_session_select(self, session_id: str):
        """Log session selection"""
        self._log("SESSION", "Session selected", {"session_id": session_id})

    def log_mode_change(self, old_mode: str, new_mode: str):
        """Log chat mode change"""
        self._log("SESSION", "Mode changed", {"from": old_mode, "to": new_mode})

    # Chat logging
    def log_chat_message(self, session_id: str, message: str, mode: str):
        """Log chat message"""
        self._log("CHAT", "Message sent", {
            "session_id": session_id,
            "mode": mode,
            "length": len(message)
        })

    def log_chat_response(self, session_id: str, response: str, mode: str):
        """Log chat response received"""
        self._log("CHAT", "Response received", {
            "session_id": session_id,
            "mode": mode,
            "length": len(response)
        })

    # Command logging
    def log_command(self, command: str, args: Optional[str] = None):
        """Log command execution"""
        msg = f"Command executed | command={command}"
        if args:
            msg += f", args={args}"
        self._log("COMMAND", msg)

    # Error logging
    def log_error(self, error_type: str, message: str, context: Optional[Dict[str, Any]] = None):
        """Log error"""
        self._log("ERROR", f"{error_type}: {message}", context)

    def log_api_error(self, endpoint: str, status_code: int, error_msg: str):
        """Log API error"""
        self._log("ERROR", "API error", {
            "endpoint": endpoint,
            "status_code": status_code,
            "error": error_msg
        })

    # File operations
    def log_export(self, project_id: str, format_type: str, filename: str):
        """Log export operation"""
        self._log("EXPORT", "Project exported", {
            "project_id": project_id,
            "format": format_type,
            "filename": filename
        })

    def get_recent_logs(self, num_lines: int = 5) -> list:
        """Get recent log entries"""
        try:
            if not self.log_file.exists():
                return []

            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                return [line.rstrip() for line in lines[-num_lines:]]
        except Exception:
            return []

    def clear_logs(self):
        """Clear all log entries"""
        try:
            if self.log_file.exists():
                self.log_file.write_text("")
                return True
        except Exception:
            pass
        return False

    def get_log_file_path(self) -> str:
        """Get path to log file"""
        return str(self.log_file)


# Global logger instance
_cli_logger: Optional[CLILogger] = None


def get_cli_logger() -> CLILogger:
    """Get or create global CLI logger instance"""
    global _cli_logger
    if _cli_logger is None:
        _cli_logger = CLILogger(enabled=False)  # Default off
    return _cli_logger
