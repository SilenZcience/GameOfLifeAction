from __future__ import annotations

import sys
from pathlib import Path


repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from game_of_life_action.iteration import iteration_image_content, update_iteration


def IterationImageContent(r: int, g: int, b: int, *_args) -> str:
    return iteration_image_content(r, g, b)


def updateIteration(imageFile: str, color: tuple, increment: bool) -> None:
    update_iteration(Path(imageFile), color, increment)
