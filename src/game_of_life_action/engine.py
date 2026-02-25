from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import convolve

from .config import Settings
from .iteration import update_iteration

_FALLBACK_CDEAD:  tuple[int, int, int, int] = (255, 254, 254, 255)
_FALLBACK_CDYING: tuple[int, int, int, int] = (40,  57,  74,  255)
_FALLBACK_CALIVE: tuple[int, int, int, int] = (65,  183, 130, 255)


def tracelog(
    *args: object,
    sep: str | None = " ",
    end: str | None = "\n",
    flush: bool = False,
) -> None:
    print("TraceLog:", *args, sep=sep, end=end, flush=flush)


class GameOfLifeEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.canvas_size = settings.canvas
        self.cell_grid = settings.grid
        self.cell_size = self._define_cell_size()

        self.target_image = self.settings.path / f"{self.settings.name}.png"
        self.target_iteration_image = self.settings.path / f"{self.settings.name}_Iteration.svg"

        self.kernel = np.ones((3, 3), dtype=np.uint8)
        self.kernel[1, 1] = 0

    def run(self) -> None:
        if self.settings.gif:
            self.create_gif(self.settings.gif)
            return

        if self.settings.from_transition and self.settings.to_transition:
            self.create_transition(self.settings.from_transition, self.settings.to_transition)
            return

        if self.target_image.exists():
            try:
                tracelog("reading game state...")
                cells, _, overlay_mask, source_pixels = self.init_running_game(self.target_image)
                prev_image = self.generate_image(cells)
                tracelog("updating game cycle...")
                cells = next(self.update_game(cells))
                tracelog("generating new image...")
                image = self.generate_image(cells)

                if np.array_equal(np.asarray(prev_image), np.asarray(image)):
                    tracelog("game finished, only still-lifes or no lifes")
                    tracelog("starting over...")
                    self.start_new_game(self.target_image)
                    tracelog("resetting index counter...")
                    update_iteration(self.target_iteration_image, self.settings.calive, False)
                else:
                    image = self._apply_overlay(image, overlay_mask, source_pixels)
                    tracelog("saving image...")
                    image.save(self.target_image)
                    tracelog("updating index counter...")
                    update_iteration(self.target_iteration_image, self.settings.calive, True)
            except Exception as exc:
                tracelog("an error occured:", exc)
                tracelog("restarting...")
                self.start_new_game(self.target_image)
                tracelog("resetting index counter...")
                update_iteration(self.target_iteration_image, self.settings.calive, False)
        else:
            tracelog("starting new game...")
            self.start_new_game(self.target_image)
            tracelog("generating index counter...")
            update_iteration(self.target_iteration_image, self.settings.calive, False)

    def _define_cell_size(self) -> tuple[int, int]:
        cell_h = int(np.ceil(self.canvas_size[0] / self.cell_grid[0]))
        cell_w = int(np.ceil(self.canvas_size[1] / self.cell_grid[1]))
        return (cell_h, cell_w)

    def update_game(self, cells: np.ndarray):
        while True:
            num_alive = convolve(cells, self.kernel, mode="constant")
            cells = (((cells) & (num_alive == 2)) | (num_alive == 3)).astype(np.uint8)

            num_alive = convolve(cells, self.kernel, mode="constant")
            cells[(cells == 1) & ((num_alive < 2) | (num_alive > 3))] = 2

            yield cells
            cells[cells > 1] = 1

    def generate_image(self, cells: np.ndarray) -> Image.Image:
        color_dead = self.settings.cdead
        color_alive = self.settings.calive
        color_dying = self.settings.cdying

        array = np.zeros([*cells.shape, 4], dtype=np.uint8)
        array[cells == 0] = color_dead
        array[cells == 1] = color_alive
        array[cells == 2] = color_dying
        array = array.repeat(self.cell_size[0], axis=0).repeat(self.cell_size[1], axis=1)
        array = array[: self.canvas_size[0], : self.canvas_size[1]]
        return Image.fromarray(array)

    def _resolve_colors(self, pixel_array: np.ndarray | None) -> None:
        """When auto_colors is True, detect the 3 most frequent RGBA values in
        *pixel_array* (at cell resolution) and assign them as cdead (most
        common), calive (second), cdying (third).  Falls back to hardcoded
        defaults when no pixel data is available."""
        if not self.settings.auto_colors:
            return
        if pixel_array is not None:
            sampled = pixel_array[:: self.cell_size[0], :: self.cell_size[1]]
            flat = sampled.reshape(-1, 4)
            unique_colors, counts = np.unique(flat, axis=0, return_counts=True)
            order = np.argsort(counts)[::-1]
            top: list[tuple[int, int, int, int]] = [
                (int(unique_colors[i, 0]), int(unique_colors[i, 1]),
                 int(unique_colors[i, 2]), int(unique_colors[i, 3]))
                for i in order[:3]
            ]
        else:
            top = []
        fallbacks = [_FALLBACK_CDEAD, _FALLBACK_CALIVE, _FALLBACK_CDYING]
        while len(top) < 3:
            top.append(fallbacks[len(top)])
        self.settings.cdead  = top[0]
        self.settings.calive = top[1]
        self.settings.cdying = top[2]
        tracelog("Resolved colors:", "cdead =", self.settings.cdead, ", calive =", self.settings.calive, ", cdying =", self.settings.cdying)

    def _extract_overlay(self, pixel_array: np.ndarray) -> np.ndarray:
        """Return a boolean mask (H, W) that is True for every pixel whose
        colour is not exactly one of cdead / calive / cdying.  Those pixels
        are considered foreign overlay content and must be preserved across
        game cycles."""
        cdead  = np.array(self.settings.cdead,  dtype=np.uint8)
        calive = np.array(self.settings.calive, dtype=np.uint8)
        cdying = np.array(self.settings.cdying, dtype=np.uint8)
        is_known = (
            np.all(pixel_array == cdead,  axis=-1) |
            np.all(pixel_array == calive, axis=-1) |
            np.all(pixel_array == cdying, axis=-1)
        )
        return ~is_known  # type: ignore[return-value]

    def _apply_overlay(
        self,
        image: Image.Image,
        overlay_mask: np.ndarray,
        source_pixels: np.ndarray,
    ) -> Image.Image:
        """Composite the overlay pixels from *source_pixels* on top of *image*
        at every position where *overlay_mask* is True."""
        arr = np.array(image)
        arr[overlay_mask] = source_pixels[overlay_mask]
        return Image.fromarray(arr)

    def init_convert_game(
        self, image: Image.Image
    ) -> tuple[np.ndarray, Image.Image, np.ndarray, np.ndarray]:
        """Convert a PIL image into a cell-grid array.

        Returns
        -------
        cells         : (rows, cols) uint8 game array
        image         : the original PIL image (unchanged)
        overlay_mask  : (H, W) bool — True where the pixel is foreign overlay
        source_pixels : (H, W, 4) uint8 — original pixel data for compositing
        """
        source_pixels = np.asarray(image).copy()
        if source_pixels.shape != (*self.canvas_size, 4):
            self.canvas_size = (source_pixels.shape[0], source_pixels.shape[1])
            if not self.settings.grid_explicit:
                self.cell_grid = (source_pixels.shape[0], source_pixels.shape[1])
            self.cell_size = self._define_cell_size()
            tracelog("Modified canvas_size:", self.canvas_size)

        self._resolve_colors(source_pixels)
        overlay_mask = self._extract_overlay(source_pixels)

        # Replace overlay pixels with cdead so game logic sees them as dead cells
        game_pixels = source_pixels.copy()
        game_pixels[overlay_mask] = self.settings.cdead

        downsampled = game_pixels[:: self.cell_size[0], :: self.cell_size[1]]
        current_array = (downsampled != self.settings.cdead).any(-1).astype(np.uint8)
        return current_array, image, overlay_mask, source_pixels

    def init_running_game(
        self, image_file: Path
    ) -> tuple[np.ndarray, Image.Image, np.ndarray, np.ndarray]:
        image = Image.open(image_file).convert("RGBA")
        return self.init_convert_game(image)

    def init_new_game(self) -> np.ndarray:
        return np.random.default_rng().integers(0, 2, self.cell_grid, dtype=np.uint8)

    def start_new_game(self, target_image: Path) -> None:
        image = self.generate_image(self.init_new_game())
        image.save(target_image)

    def read_gif(self, filename: Path, as_numpy: bool = True, split: bool = True) -> list:
        gif_image = Image.open(filename)
        images = []
        total_frames = int(getattr(gif_image, "n_frames", 1))
        n_frames = (total_frames // 2) + 1 if split else total_frames

        for frame in range(n_frames):
            gif_image.seek(frame)
            image = gif_image.convert("RGBA")
            if as_numpy:
                image = np.asarray(image)
                if len(image.shape) == 0:
                    raise MemoryError("Too little memory to convert PIL image to array")
            images.append(image)
        return images

    def create_gif(self, gif_path: Path) -> None:
        gif_split = gif_path.with_suffix("")

        if gif_path.suffix.upper() == ".GIF":
            images = self.read_gif(gif_path, as_numpy=False)
            cells, _, overlay_mask, source_pixels = self.init_convert_game(images[-1])
            gif_length = self.settings.gif_length
            if gif_length < 0:
                gif_length = len(images) + 1
        else:
            images = []
            cells, current_image, overlay_mask, source_pixels = self.init_running_game(gif_path)
            tracelog("Generating image ", 1, "/", self.settings.gif_length, sep="")
            images.append(current_image)
            gif_length = self.settings.gif_length

        start_frame = len(images)
        cell_gen = self.update_game(cells)
        for frame_index in range(start_frame, gif_length):
            tracelog("Generating image ", frame_index + 1, "/", gif_length, sep="")
            cells = next(cell_gen)
            images.append(self.generate_image(cells))

        # Apply the overlay on top of every generated frame
        images = [self._apply_overlay(img, overlay_mask, source_pixels) for img in images]

        frame_pause = max((400 // self.settings.gif_speed), 0)
        frame_pause_images = [images[0] for _ in range(frame_pause)]
        tracelog("Saving gif...")

        images[0].save(
            str(gif_split) + ".gif",
            save_all=True,
            append_images=frame_pause_images + images[1:] + images[-2::-1],
            optimize=False,
            duration=self.settings.gif_speed,
            loop=0,
        )

    def generate_transition(
        self,
        cells_from: np.ndarray,
        cells_to: np.ndarray,
        probability: float,
        previous_mask: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng()
        random_modifier = rng.choice([False, True], size=cells_from.shape, p=[0.25, 0.75])
        previous_mask[previous_mask] = random_modifier[previous_mask]
        random_mask = rng.choice(
            [False, True], size=cells_from.shape, p=[1 - probability, probability]
        )
        random_mask[previous_mask] = True
        transition_cells = np.copy(cells_from)
        transition_cells[random_mask] = cells_to[random_mask]
        return transition_cells, random_mask

    def create_transition(self, from_image: Path, to_image: Path) -> None:
        gif_split = from_image.with_suffix("")

        cells_from, current_image_from, overlay_mask_from, source_pixels_from = self.init_running_game(from_image)
        cells_to,   current_image_to,   overlay_mask_to,   source_pixels_to   = self.init_running_game(to_image)

        images_from = [current_image_from]
        images_to = [current_image_to]
        images_transition = []
        tracelog(from_image, to_image)

        frame_count_split = self.settings.gif_length // 2
        frame_count_transition = max(5, self.settings.gif_length // 10)

        cell_gen_from = self.update_game(cells_from)
        cell_gen_to = self.update_game(cells_to)

        for i in range(frame_count_split):
            tracelog("Generating image (from) ", i + 1, "/", self.settings.gif_length, sep="")
            cells_from = next(cell_gen_from)
            images_from.append(self.generate_image(cells_from))

        for i in range(frame_count_split, self.settings.gif_length):
            tracelog("Generating image  (to)  ", i + 1, "/", self.settings.gif_length, sep="")
            cells_to = next(cell_gen_to)
            images_to.append(self.generate_image(cells_to))

        random_mask = cells_from == cells_to
        for i in range(1, frame_count_transition + 1):
            tracelog("Generating transition   ", i, "/", frame_count_transition, sep="")
            probability = i / (frame_count_transition + 1)
            if probability < 0.1:
                continue
            if probability > 0.9:
                break
            cells_transition, random_mask = self.generate_transition(
                cells_from, cells_to, probability, random_mask
            )
            images_transition.append(self.generate_image(cells_transition))

        # Apply each image's own overlay; transition frames inherit the "from" overlay
        images_from       = [self._apply_overlay(img, overlay_mask_from, source_pixels_from) for img in images_from]
        images_to         = [self._apply_overlay(img, overlay_mask_to,   source_pixels_to)   for img in images_to]
        images_transition = [self._apply_overlay(img, overlay_mask_from, source_pixels_from) for img in images_transition]

        frame_pause = max((600 // self.settings.gif_speed), 0)
        frame_pause_from = [images_from[0] for _ in range(frame_pause)]
        frame_pause_to = [images_to[0] for _ in range(frame_pause)]
        tracelog("Saving gif...")

        images_from[0].save(
            str(gif_split) + "-transition.gif",
            save_all=True,
            append_images=(
                frame_pause_from
                + images_from[1:]
                + images_transition
                + images_to[::-1]
                + frame_pause_to
                + images_to[1:]
                + images_transition[::-1]
                + images_from[:0:-1]
            ),
            optimize=False,
            duration=self.settings.gif_speed,
            loop=0,
        )
