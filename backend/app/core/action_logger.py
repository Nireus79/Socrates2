"""
ActionLogger - Centralized logging for all user-facing actions.

Tracks and logs the completion of important operations so users can monitor
the background workflow progress. Supports centralized enable/disable control.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from datetime import datetime

# Global state for action logging
_action_logging_enabled = True
_action_logger = None

def initialize_action_logger(enabled: bool = True, log_level: str = "INFO"):
    """
    Initialize the action logger with configuration.

    Args:
        enabled: Whether action logging is enabled
        log_level: Logging level (INFO, DEBUG, WARNING)
    """
    global _action_logging_enabled, _action_logger

    _action_logging_enabled = enabled

    # Create action logger (separate from standard logger)
    _action_logger = logging.getLogger("actions")

    # Clear existing handlers
    _action_logger.handlers.clear()

    if enabled:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - [ACTION] %(message)s",
            datefmt="%H:%M:%S"
        )
        handler.setFormatter(formatter)
        _action_logger.addHandler(handler)
        _action_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    else:
        # Add null handler when disabled
        _action_logger.addHandler(logging.NullHandler())
        _action_logger.setLevel(logging.CRITICAL + 1)

def toggle_action_logging(enabled: bool) -> bool:
    """
    Toggle action logging on/off at runtime.

    Args:
        enabled: True to enable, False to disable

    Returns:
        New state of action logging
    """
    global _action_logging_enabled
    _action_logging_enabled = enabled

    # Reinitialize logger with new state
    if _action_logger:
        if enabled:
            _action_logger.handlers.clear()
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - [ACTION] %(message)s",
                datefmt="%H:%M:%S"
            )
            handler.setFormatter(formatter)
            _action_logger.addHandler(handler)
            _action_logger.setLevel(logging.INFO)
        else:
            _action_logger.handlers.clear()
            _action_logger.addHandler(logging.NullHandler())
            _action_logger.setLevel(logging.CRITICAL + 1)

    return _action_logging_enabled

def is_action_logging_enabled() -> bool:
    """Check if action logging is currently enabled."""
    return _action_logging_enabled

def get_action_logger():
    """Get the action logger instance."""
    global _action_logger
    if _action_logger is None:
        initialize_action_logger()
    return _action_logger

# Initialize with defaults (will be updated during app startup)
initialize_action_logger(enabled=True)


class ActionLogger:
    """Centralized action logging for monitoring workflow progress."""

    @staticmethod
    def auth(action: str, user_id: Optional[str] = None, success: bool = True, **details):
        """Log authentication action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} AUTH: {action}"
        if user_id:
            msg += f" (user: {user_id[:8]}...)"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def project(action: str, project_id: Optional[str] = None, project_name: Optional[str] = None,
                success: bool = True, **details):
        """Log project-related action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} PROJECT: {action}"
        if project_name:
            msg += f" ({project_name})"
        elif project_id:
            msg += f" ({project_id[:8]}...)"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def session(action: str, session_id: Optional[str] = None, mode: Optional[str] = None,
                success: bool = True, **details):
        """Log session action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} SESSION: {action}"
        if mode:
            msg += f" ({mode})"
        elif session_id:
            msg += f" ({session_id[:8]}...)"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def specs(action: str, count: Optional[int] = None, success: bool = True, **details):
        """Log specification extraction action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} SPECS: {action}"
        if count is not None:
            msg += f" ({count} extracted)"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def agent(action: str, agent_id: Optional[str] = None, agent_name: Optional[str] = None,
              success: bool = True, **details):
        """Log agent action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} AGENT: {action}"
        if agent_name:
            msg += f" ({agent_name})"
        elif agent_id:
            msg += f" ({agent_id})"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def llm(action: str, model: Optional[str] = None, tokens: Optional[int] = None,
            success: bool = True, **details):
        """Log LLM interaction."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} LLM: {action}"
        if model:
            msg += f" ({model})"
        if tokens is not None:
            msg += f" | tokens={tokens}"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def question(action: str, category: Optional[str] = None, success: bool = True, **details):
        """Log question generation action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} QUESTION: {action}"
        if category:
            msg += f" ({category})"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def conflict(action: str, count: Optional[int] = None, success: bool = True, **details):
        """Log conflict detection action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} CONFLICT: {action}"
        if count is not None:
            msg += f" ({count} found)"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def database(action: str, table: Optional[str] = None, rows: Optional[int] = None,
                 success: bool = True, **details):
        """Log database action."""
        if not _action_logging_enabled:
            return
        status = "✓" if success else "✗"
        msg = f"{status} DB: {action}"
        if table:
            msg += f" ({table})"
        if rows is not None:
            msg += f" | rows={rows}"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

    @staticmethod
    def error(action: str, error: str, context: Optional[str] = None, **details):
        """Log error action."""
        msg = f"✗ ERROR: {action} | {error}"
        if context:
            msg += f" ({context})"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().error(msg)

    @staticmethod
    def warning(action: str, warning: str, **details):
        """Log warning action."""
        msg = f"⚠ WARNING: {action} | {warning}"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().warning(msg)

    @staticmethod
    @contextmanager
    def timed_action(action: str, category: str = "ACTION", **details):
        """Context manager to log timed actions with duration."""
        start_time = time.time()
        msg = f"→ {category}: {action} (started)"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)

        try:
            yield
            duration = time.time() - start_time
            msg = f"✓ {category}: {action} (completed in {duration:.2f}s)"
            if details:
                msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
            get_action_logger().info(msg)
        except Exception as e:
            duration = time.time() - start_time
            msg = f"✗ {category}: {action} (failed after {duration:.2f}s) | {str(e)}"
            if details:
                msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
            get_action_logger().error(msg)
            raise

    @staticmethod
    def progress(step: int, total: int, action: str, **details):
        """Log progress of multi-step action."""
        percent = int((step / total) * 100)
        msg = f"⊢ PROGRESS: {action} ({step}/{total}) [{percent}%]"
        if details:
            msg += f" | {', '.join(f'{k}={v}' for k, v in details.items())}"
        get_action_logger().info(msg)


# Convenience functions for direct use
def log_auth(action: str, **kwargs):
    """Log authentication action."""
    ActionLogger.auth(action, **kwargs)


def log_project(action: str, **kwargs):
    """Log project action."""
    ActionLogger.project(action, **kwargs)


def log_session(action: str, **kwargs):
    """Log session action."""
    ActionLogger.session(action, **kwargs)


def log_specs(action: str, **kwargs):
    """Log specification action."""
    ActionLogger.specs(action, **kwargs)


def log_agent(action: str, **kwargs):
    """Log agent action."""
    ActionLogger.agent(action, **kwargs)


def log_llm(action: str, **kwargs):
    """Log LLM action."""
    ActionLogger.llm(action, **kwargs)


def log_question(action: str, **kwargs):
    """Log question action."""
    ActionLogger.question(action, **kwargs)


def log_conflict(action: str, **kwargs):
    """Log conflict action."""
    ActionLogger.conflict(action, **kwargs)


def log_database(action: str, **kwargs):
    """Log database action."""
    ActionLogger.database(action, **kwargs)


def log_error(action: str, error: str, **kwargs):
    """Log error."""
    ActionLogger.error(action, error, **kwargs)


def log_warning(action: str, warning: str, **kwargs):
    """Log warning."""
    ActionLogger.warning(action, warning, **kwargs)
