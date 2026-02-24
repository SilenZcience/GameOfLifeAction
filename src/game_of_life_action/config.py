from __future__ import annotations

import argparse
import atexit
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import cast
from typing import Sequence

from PIL.ImageColor import getcolor

_ALLOWED_EXT = {".BMP", ".JPEG", ".PNG", ".SPIDER", ".TIFF", ".GIF"}
_SVG_EXT = ".SVG"


@dataclass(slots=True)
class Settings:
    path: Path
    cdead: tuple[int, int, int, int]
    cdying: tuple[int, int, int, int]
    calive: tuple[int, int, int, int]
    canvas: tuple[int, int]
    grid: tuple[int, int]
    gif: Path | None
    gif_length: int
    gif_speed: int
    from_transition: Path | None
    to_transition: Path | None
    name: str = field(default="GameOfLife")
    auto_colors: bool = field(default=False)


class ConfigError(ValueError):
    pass


def _parse_color(raw: str, name: str) -> tuple[int, int, int, int]:
    raw = raw.strip()
    if not raw:
        raise ConfigError(f"Invalid {name}: expected a color value")
    try:
        color = cast(tuple[int, int, int, int], getcolor(raw, "RGBA"))
    except Exception as exc:  # pragma: no cover
        raise ConfigError(f"Invalid {name}: expected a color value") from exc
    return color


def _parse_int_pair(raw: str, name: str) -> tuple[int, int]:
    try:
        values = tuple(int(item.strip()) for item in raw.split(","))
    except Exception as exc:
        raise ConfigError(f"Invalid {name}: expected a,b") from exc

    if len(values) != 2 or values[0] <= 0 or values[1] <= 0:
        raise ConfigError(f"Invalid {name}: expected two positive integers")
    return values


def _resolve_svg(value: str, dir: Path, name: str) -> Path:
    """Convert an SVG file path or URL to a PNG in *dir* and return its path.
    The temp file is registered for deletion on process exit."""
    from .svg import svg_to_png  # local import to avoid circular deps
    source: Path | str = Path(value).expanduser().resolve()
    if source.exists() and source.is_file():
        stem = source.stem
    else:
        source = value
        stem = name
    out = dir / f"{stem}.png"
    print(f"Converting SVG to PNG: {value}")
    svg_to_png(source, out)
    atexit.register(lambda p: p.unlink(missing_ok=True), out)
    return out


def _validate_image_file(path: Path, field_name: str) -> Path:
    if not path.exists() or not path.is_file():
        raise ConfigError(f"Invalid {field_name}: file does not exist")
    if path.suffix.upper() not in _ALLOWED_EXT:
        raise ConfigError(
            f"Invalid {field_name}: unsupported file type. Allowed: {sorted(_ALLOWED_EXT)}"
        )
    return path


def parse_args(argv: Sequence[str] | None = None, *, default_path: Path) -> Settings:
    parser = argparse.ArgumentParser(description="Generate and evolve a Game of Life image")

    parser.add_argument("-p", "-path", default=str(default_path), dest="path")
    parser.add_argument("-name", default="GameOfLife", dest="name")
    parser.add_argument("-cdead", default=None)
    parser.add_argument("-cdying", default=None)
    parser.add_argument("-calive", default=None)
    parser.add_argument("-canvas", default="420,1200")
    parser.add_argument("-grid", default="84,240")
    parser.add_argument("-gif", default="")
    parser.add_argument("-gifLength", default=10, type=int)
    parser.add_argument("-gifSpeed", default=100, type=int)
    parser.add_argument("-from", default="", dest="from_transition")
    parser.add_argument("-to", default="", dest="to_transition")

    param = parser.parse_args(argv)

    path = Path(param.path).expanduser().resolve()
    if not path.exists() or not path.is_dir():
        raise ConfigError("Invalid PATH: choose an existing folder")

    auto_colors = param.cdead is None and param.cdying is None and param.calive is None
    cdead  = _parse_color(param.cdead,  "-cdead")  if param.cdead  else (255, 254, 254, 255)
    cdying = _parse_color(param.cdying, "-cdying") if param.cdying else (40,  57,  74,  255)
    calive = _parse_color(param.calive, "-calive") if param.calive else (65,  183, 130, 255)
    canvas = _parse_int_pair(param.canvas, "-canvas")
    grid = _parse_int_pair(param.grid, "-grid")

    gif_raw = param.gif
    gif: Path | None = None
    if gif_raw:
        if gif_raw.upper().endswith(_SVG_EXT) or gif_raw.startswith(("http://", "https://")):
            gif = _resolve_svg(gif_raw, path, param.name)
        else:
            gif = _validate_image_file(Path(gif_raw).expanduser().resolve(), "-gif")

    from_raw = param.from_transition
    from_transition: Path | None = None
    if from_raw:
        if from_raw.upper().endswith(_SVG_EXT) or from_raw.startswith(("http://", "https://")):
            from_transition = _resolve_svg(from_raw, path, param.name)
        else:
            from_transition = Path(from_raw).expanduser().resolve()

    to_raw = param.to_transition
    to_transition: Path | None = None
    if to_raw:
        if to_raw.upper().endswith(_SVG_EXT) or to_raw.startswith(("http://", "https://")):
            to_transition = _resolve_svg(to_raw, path, param.name)
        else:
            to_transition = Path(to_raw).expanduser().resolve()

    if bool(from_transition) != bool(to_transition):
        raise ConfigError("Transition requires both -from and -to")

    if from_transition and to_transition:
        from_transition = _validate_image_file(from_transition, "-from")
        to_transition = _validate_image_file(to_transition, "-to")

    if not auto_colors and (gif or (from_transition and to_transition)):
        for palette in (cdead, cdying, calive):
            if palette[3] != 255:
                raise ConfigError("GIF/transition generation requires alpha FF")

    return Settings(
        path=path,
        cdead=cdead,
        cdying=cdying,
        calive=calive,
        canvas=canvas,
        grid=grid,
        gif=gif,
        gif_length=param.gifLength,
        gif_speed=param.gifSpeed,
        from_transition=from_transition,
        to_transition=to_transition,
        name=param.name,
        auto_colors=auto_colors,
    )
