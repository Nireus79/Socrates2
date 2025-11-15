#!/usr/bin/env python3
"""
Socrates CLI Entry Point

This script serves as the entry point for the Socrates CLI application.
It properly handles imports from the src/ package and launches the main application.

Usage:
    python socrates.py [--api-url URL] [--debug]
"""

import sys
from pathlib import Path

# Add src/ to Python path so imports work correctly
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def main():
    """Launch the Socrates CLI application"""
    try:
        # Import here after path is set up
        from Socrates import SocratesCLI

        # Create and run the CLI
        cli = SocratesCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
