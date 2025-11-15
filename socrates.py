#!/usr/bin/env python3
"""
Socrates CLI Entry Point

This script serves as the entry point for the Socrates CLI application.
It properly handles imports from the src/ package and launches the main application.

Usage:
    python socrates.py [--api-url URL] [--debug]
"""

import sys
import os
import argparse
from pathlib import Path

# Add src/ to Python path so imports work correctly
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def main():
    """Launch the Socrates CLI application"""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Socrates CLI Application")
    parser.add_argument(
        "--api-url",
        default=os.getenv("SOCRATES_API_URL", "http://localhost:8000"),
        help="API URL for the Socrates backend (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=os.getenv("DEBUG", "").lower() == "true",
        help="Enable debug mode"
    )
    parser.add_argument(
        "--no-auto-start",
        action="store_true",
        help="Do not automatically start the backend server"
    )
    args = parser.parse_args()

    try:
        # Import here after path is set up
        from Socrates import SocratesCLI

        # Create and run the CLI with parsed arguments
        cli = SocratesCLI(
            api_url=args.api_url,
            debug=args.debug,
            auto_start_server=not args.no_auto_start
        )
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
