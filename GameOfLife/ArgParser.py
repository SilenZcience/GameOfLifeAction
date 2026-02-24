from __future__ import annotations

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from game_of_life_action.config import ConfigError, Settings, parse_args

_COLOR_ARGS = {"-cdead", "-cdying", "-calive"}
_default_path = Path(__file__).resolve().parent


def _split_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    """Split legacy argv where color args accept '#light,#dark' into two
    single-color argvs understood by parse_args."""
    light_argv: list[str] = []
    dark_argv: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in _COLOR_ARGS and i + 1 < len(argv):
            parts = [p.strip() for p in argv[i + 1].split(",") if p.strip()]
            light_argv += [arg, parts[0]]
            dark_argv  += [arg, parts[1] if len(parts) > 1 else parts[0]]
            i += 2
        else:
            light_argv.append(arg)
            dark_argv.append(arg)
            i += 1
    return light_argv, dark_argv


def parseArgs() -> tuple[Settings, Settings]:
    light_argv, dark_argv = _split_argv(sys.argv[1:])
    try:
        settings_light = parse_args(light_argv, default_path=_default_path)
        settings_light.name = "GameOfLifeLight"
        settings_dark  = parse_args(dark_argv,  default_path=_default_path)
        settings_dark.name = "GameOfLifeDark"
    except ConfigError as exc:
        print(exc)
        raise SystemExit(2) from exc
    return settings_light, settings_dark
