"""
Socrates CLI - Modular command system.

This package contains the modular CLI architecture with:
- base: CommandHandler abstract base class
- registry: CommandRegistry for auto-discovering commands
- commands: Individual command implementations
- utils: Shared utilities and helpers
"""

from cli.base import CommandHandler
from cli.registry import CommandRegistry

__all__ = ["CommandHandler", "CommandRegistry"]
