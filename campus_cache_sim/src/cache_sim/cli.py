import sys
from .simulator import run


def main(argv=None):
    argv = argv or sys.argv[1:]
    if len(argv) != 1:
        print("usage: python -m src.cache_sim.cli <operations.txt>")
        return 2
    with open(argv[0]) as f:
        for entry in run(f):
            print(entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
