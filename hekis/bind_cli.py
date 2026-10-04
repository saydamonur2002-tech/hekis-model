"""Gozleme bagli kosu.

    python -m hekis.bind_cli
"""

from hekis.bind import matrix, run_bound, sensitivity


def main() -> int:
    print(matrix())
    print()
    print(sensitivity())
    print()
    for report in run_bound():
        print(report)
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
