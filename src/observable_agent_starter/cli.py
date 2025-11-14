"""
Command-line interface.

Minimal CLI stub for your agent project. Customize this for your specific commands.
"""

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    from . import __version__

    parser = argparse.ArgumentParser(
        prog="observable-agent",
        description="LLM agent with Langfuse observability",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    _args = parser.parse_args(argv)  # Add your custom arguments here

    # Default behavior - customize this with your agent commands
    print(f"observable-agent v{__version__}")
    print("Ready. Add your commands to cli.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())
