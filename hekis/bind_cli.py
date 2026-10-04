"""Gozleme bagli kosu.

    python -m hekis.bind_cli
"""

from hekis.bind import run_bound


def main() -> int:
    for report in run_bound():
        print(report)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
