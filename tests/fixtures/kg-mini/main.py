"""Entry point wiring pkg.core into a small demo run."""
from pkg.core import run_job


def main() -> None:
    print(run_job("Hello Graph"))


if __name__ == "__main__":
    main()
