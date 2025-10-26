"""CLI entry point for the routing agent."""

import logging

from .agent import StarterAgent


def main() -> None:
    """Run the starter agent with an example request."""
    logging.basicConfig(level=logging.INFO)
    agent = StarterAgent()
    example = "The invoice shows an extra fee on my account."
    # Prefer calling the module directly instead of .forward(...)
    result = agent(request=example)
    print(result)


if __name__ == "__main__":
    main()

