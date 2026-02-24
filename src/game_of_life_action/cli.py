from __future__ import annotations

import sys
from pathlib import Path

from .config import ConfigError, parse_args
from .engine import GameOfLifeEngine


def main(argv: list[str] | None = None) -> int:
    default_path = Path(__file__).resolve().parents[2] / "GameOfLife"

    try:
        settings = parse_args(argv, default_path=default_path)
    except ConfigError as exc:
        print(exc)
        return 2

    try:
        engine = GameOfLifeEngine(settings)
        engine.run()
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print("Game of Life failed:", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
