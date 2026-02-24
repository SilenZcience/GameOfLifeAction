from __future__ import annotations

import sys
from pathlib import Path


repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from ArgParser import parseArgs
from game_of_life_action.engine import GameOfLifeEngine


if __name__ == "__main__":
    for settings in parseArgs():
        try:
            engine = GameOfLifeEngine(settings)
            engine.run()
        except KeyboardInterrupt as exc:
            raise SystemExit(130) from exc
        except Exception as exc:
            print("Game of Life failed:", exc)
            raise SystemExit(1) from exc
