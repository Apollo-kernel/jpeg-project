from __future__ import annotations

from typing import Callable

import numpy as np


def _validate_shape(width: int, height: int) -> None:
    if width <= 0 or height <= 0:
        raise ValueError(f"width and height must be positive, got {width=}, {height=}")


def make_constant(width: int, height: int, value: int) -> np.ndarray:
    _validate_shape(width, height)
    return np.full((height, width), np.uint8(value), dtype=np.uint8)


def make_horizontal_gradient(width: int, height: int) -> np.ndarray:
    _validate_shape(width, height)
    row = np.linspace(0, 255, width, dtype=np.uint8)
    return np.tile(row[None, :], (height, 1))


def make_vertical_gradient(width: int, height: int) -> np.ndarray:
    _validate_shape(width, height)
    col = np.linspace(0, 255, height, dtype=np.uint8)
    return np.tile(col[:, None], (1, width))


def make_checkerboard(
    width: int,
    height: int,
    a: int = 0,
    b: int = 255,
    block: int = 1,
) -> np.ndarray:
    _validate_shape(width, height)
    if block <= 0:
        raise ValueError(f"block must be positive, got {block}")
    y = np.arange(height)[:, None] // block
    x = np.arange(width)[None, :] // block
    mask = ((x + y) % 2).astype(np.uint8)
    arr = np.where(mask == 0, a, b)
    return np.asarray(arr, dtype=np.uint8)


def make_random(width: int, height: int, seed: int = 0) -> np.ndarray:
    _validate_shape(width, height)
    rng = np.random.default_rng(seed)
    return rng.integers(0, 256, size=(height, width), dtype=np.uint8)


def make_from_function(
    width: int,
    height: int,
    fn: Callable[[int, int], int],
) -> np.ndarray:
    """
    Build a uint8 image from a Python function fn(y, x) -> int.
    """
    _validate_shape(width, height)
    arr = np.zeros((height, width), dtype=np.uint8)
    for y in range(height):
        for x in range(width):
            arr[y, x] = np.uint8(fn(y, x))
    return arr
