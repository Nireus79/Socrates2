"""Socrates2 CLI module.

Command-line interface for managing Socrates2 projects, specifications, and configurations.
"""

try:
    from .main import cli
    __all__ = ["cli"]
except ImportError:
    # Click not installed yet
    __all__ = []
