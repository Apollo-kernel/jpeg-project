from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def load_image_as_grayscale(path: str | Path) -> np.ndarray:
    """
    Load an image file and return a uint8 grayscale array with shape (H, W).
    """
    img = Image.open(path).convert("L")
    arr = np.asarray(img, dtype=np.uint8)
    if arr.ndim != 2:
        raise ValueError(f"Expected a grayscale 2-D array, got shape={arr.shape}")
    return arr


def save_mem(
    image: np.ndarray,
    mem_path: str | Path,
    *,
    fmt: str = "hex",
    include_dims_header: bool = False,
) -> None:
    """
    Save a uint8 grayscale image to a .mem file in row-major order.

    By default:
      - one pixel per line
      - two-digit uppercase hexadecimal
      - no header

    Example:
      00
      7F
      FF
    """
    arr = np.asarray(image)
    if arr.ndim != 2:
        raise ValueError(f"Expected shape (H, W), got {arr.shape}")
    if arr.dtype != np.uint8:
        raise TypeError(f"Expected dtype uint8, got {arr.dtype}")

    mem_path = Path(mem_path)
    lines: list[str] = []

    if include_dims_header:
        h, w = arr.shape
        lines.append(f"// HEIGHT={h}")
        lines.append(f"// WIDTH={w}")

    flat = arr.reshape(-1)
    if fmt == "hex":
        lines.extend(f"{int(v):02X}" for v in flat)
    elif fmt == "bin":
        lines.extend(f"{int(v):08b}" for v in flat)
    else:
        raise ValueError("fmt must be 'hex' or 'bin'")

    mem_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_mem(
    mem_path: str | Path,
    *,
    height: int,
    width: int,
    fmt: str = "hex",
) -> np.ndarray:
    """
    Load a .mem file back into a uint8 image of shape (height, width).
    Comment lines starting with // are ignored.
    """
    mem_path = Path(mem_path)
    values: list[int] = []
    for raw in mem_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("//"):
            continue
        if fmt == "hex":
            values.append(int(line, 16))
        elif fmt == "bin":
            values.append(int(line, 2))
        else:
            raise ValueError("fmt must be 'hex' or 'bin'")

    if len(values) != height * width:
        raise ValueError(
            f"Expected {height*width} pixels, found {len(values)} in {mem_path}"
        )

    return np.asarray(values, dtype=np.uint8).reshape(height, width)


def write_dims_file(image: np.ndarray, path: str | Path) -> None:
    arr = np.asarray(image)
    if arr.ndim != 2:
        raise ValueError(f"Expected shape (H, W), got {arr.shape}")
    h, w = arr.shape
    Path(path).write_text(f"{h} {w}\n", encoding="utf-8")


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an image to an 8-bit grayscale .mem file."
    )
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output .mem path")
    parser.add_argument(
        "--fmt",
        default="hex",
        choices=["hex", "bin"],
        help="Pixel format written to the .mem file",
    )
    parser.add_argument(
        "--dims-out",
        default=None,
        help="Optional text file for writing 'HEIGHT WIDTH'",
    )
    parser.add_argument(
        "--include-dims-header",
        action="store_true",
        help="Include comment header lines in the .mem file",
    )
    return parser


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()

    img = load_image_as_grayscale(args.input)
    save_mem(
        img,
        args.output,
        fmt=args.fmt,
        include_dims_header=args.include_dims_header,
    )

    if args.dims_out:
        write_dims_file(img, args.dims_out)

    print(f"Converted {args.input} -> {args.output}, shape={img.shape}")


if __name__ == "__main__":
    main()
