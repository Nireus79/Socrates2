"""
Socrates CLI Source Package

Main modules:
- Socrates: Core CLI application
- intent_parser: Natural language command parsing
- cli_logger: Logging utilities
- api_client_extension: Extended API client
- socrates_cli_lib: Library functions
"""

__version__ = "1.0.0"
__author__ = "Socrates Contributors"

# Import main classes for convenience
try:
    from .Socrates import SocratesCLI
    from .intent_parser import IntentParser
    from .cli_logger import get_cli_logger

    __all__ = ["SocratesCLI", "IntentParser", "get_cli_logger"]
except ImportError:
    # Allow package to be imported even if dependencies are missing
    pass
