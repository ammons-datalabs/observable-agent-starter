import logging

from .agent import ExampleAgent


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    triager = ExampleAgent()
    example = "The invoice shows an extra fee on my account."
    # Prefer calling the module directly instead of .forward(...)
    result = triager(request=example)
    print(result)


if __name__ == "__main__":
    main()

