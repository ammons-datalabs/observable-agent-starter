import logging

from .agent import AgentOpsDemo


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    triager = AgentOpsDemo()
    example = "The invoice shows an extra fee on my account."
    # Prefer calling the module directly instead of .forward(...)
    result = triager(ticket=example)
    print(result)


if __name__ == "__main__":
    main()

