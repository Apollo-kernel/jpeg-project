from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


MAXVAL = 255
NEAR = 0
RESET = 64
T1 = 3
T2 = 7
T3 = 21
MIN_C = -128
MAX_C = 127


class BitWriter:
    """
    MSB-first bit packer.

    Internally, bits are appended to a byte accumulator from MSB to LSB.
    The final partial byte is zero-padded on the right when flushed.
    """

    def __init__(self) -> None:
        self._bytes = bytearray()
        self._cur = 0
        self._nbits = 0
        self._written_bits = 0

    def write_bit(self, bit: int) -> None:
        bit = 1 if bit else 0
        self._cur = (self._cur << 1) | bit
        self._nbits += 1
        self._written_bits += 1
        if self._nbits == 8:
            self._bytes.append(self._cur & 0xFF)
            self._cur = 0
            self._nbits = 0

    def write_bits(self, value: int, nbits: int) -> None:
        if nbits < 0:
            raise ValueError("nbits must be nonnegative")
        for i in range(nbits - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def write_unary(self, q: int) -> None:
        if q < 0:
            raise ValueError("Unary code only supports q >= 0")
        for _ in range(q):
            self.write_bit(1)
        self.write_bit(0)

    def flush(self) -> None:
        if self._nbits:
            self._cur <<= (8 - self._nbits)
            self._bytes.append(self._cur & 0xFF)
            self._cur = 0
            self._nbits = 0

    def to_bytes(self) -> bytes:
        self.flush()
        return bytes(self._bytes)

    def bit_length(self) -> int:
        return self._written_bits


def save_bytes_mem(data: bytes, path: str | Path) -> None:
    txt = "\n".join(f"{b:02X}" for b in data)
    if txt:
        txt += "\n"
    Path(path).write_text(txt, encoding="utf-8")


def get_neighbors(image: np.ndarray, y: int, x: int) -> tuple[int, int, int, int]:
    """
    Return causal JPEG-LS neighbors (A, B, C, D).

      C  B  D
      A  X

    Border convention for this stage-1 model:
      - Missing A/B/C use 0
      - Missing D uses B
    """
    A = int(image[y, x - 1]) if x > 0 else 0
    B = int(image[y - 1, x]) if y > 0 else 0
    C = int(image[y - 1, x - 1]) if (y > 0 and x > 0) else 0
    D = int(image[y - 1, x + 1]) if (y > 0 and x + 1 < image.shape[1]) else B
    return A, B, C, D


def quantize_gradient(g: int) -> int:
    if g <= -T3:
        return -4
    if g <= -T2:
        return -3
    if g <= -T1:
        return -2
    if g < -NEAR:
        return -1
    if g <= NEAR:
        return 0
    if g < T1:
        return 1
    if g < T2:
        return 2
    if g < T3:
        return 3
    return 4


def normalize_context(q1: int, q2: int, q3: int) -> tuple[tuple[int, int, int], int]:
    """
    Sign-normalize the quantized gradient triple.

    Returns:
      ctx_key : normalized context tuple
      sign    : +1 or -1
    """
    if q1 < 0 or (q1 == 0 and q2 < 0) or (q1 == 0 and q2 == 0 and q3 < 0):
        return (-q1, -q2, -q3), -1
    return (q1, q2, q3), 1


def med_predictor(A: int, B: int, C: int) -> int:
    if C >= max(A, B):
        return min(A, B)
    if C <= min(A, B):
        return max(A, B)
    return A + B - C


def golomb_k(Aq: int, Nq: int) -> int:
    k = 0
    while (Nq << k) < Aq:
        k += 1
    return k


def map_error(errval: int) -> int:
    if errval >= 0:
        return 2 * errval
    return -2 * errval - 1


@dataclass
class EncodeResult:
    bitstream_bytes: bytes
    nbits: int
    trace: dict[str, np.ndarray]


class JPEGLSRegularEncoder:
    """
    Small stage-1 reference encoder.

    Scope:
      - uint8 grayscale only
      - lossless only
      - regular mode only
      - educational / bring-up reference
    """

    def __init__(self) -> None:
        self.ctx_to_idx: Dict[Tuple[int, int, int], int] = {}
        self.A: list[int] = []
        self.B: list[int] = []
        self.C: list[int] = []
        self.N: list[int] = []

    def _ctx_index(self, ctx: tuple[int, int, int]) -> int:
        if ctx not in self.ctx_to_idx:
            idx = len(self.ctx_to_idx)
            self.ctx_to_idx[ctx] = idx
            self.A.append(4)
            self.B.append(0)
            self.C.append(0)
            self.N.append(1)
        return self.ctx_to_idx[ctx]

    def encode(self, image: np.ndarray) -> EncodeResult:
        arr = np.asarray(image)
        if arr.dtype != np.uint8 or arr.ndim != 2:
            raise ValueError("image must be a uint8 array with shape (H, W)")

        h, w = arr.shape
        writer = BitWriter()

        pred = np.zeros((h, w), dtype=np.int16)
        err = np.zeros((h, w), dtype=np.int16)
        merr = np.zeros((h, w), dtype=np.uint16)
        kmap = np.zeros((h, w), dtype=np.uint8)
        ctx_id_map = np.zeros((h, w), dtype=np.int16)

        for y in range(h):
            for x in range(w):
                A, B, C, D = get_neighbors(arr, y, x)

                g1 = D - B
                g2 = B - C
                g3 = C - A

                q1 = quantize_gradient(g1)
                q2 = quantize_gradient(g2)
                q3 = quantize_gradient(g3)
                ctx_key, sign = normalize_context(q1, q2, q3)
                q = self._ctx_index(ctx_key)

                Px = med_predictor(A, B, C)
                if sign == 1:
                    Px = Px + self.C[q]
                else:
                    Px = Px - self.C[q]
                Px = min(MAXVAL, max(0, Px))

                cur = int(arr[y, x])
                Errval = cur - Px
                if sign == -1:
                    Errval = -Errval

                k = golomb_k(self.A[q], self.N[q])
                MErrval = map_error(Errval)

                unary_q = MErrval >> k
                rem = MErrval & ((1 << k) - 1) if k > 0 else 0
                writer.write_unary(unary_q)
                if k > 0:
                    writer.write_bits(rem, k)

                pred[y, x] = Px
                err[y, x] = Errval
                merr[y, x] = MErrval
                kmap[y, x] = k
                ctx_id_map[y, x] = q

                self.B[q] += Errval
                self.A[q] += abs(Errval)

                if self.B[q] <= -self.N[q]:
                    self.B[q] += self.N[q]
                    if self.C[q] > MIN_C:
                        self.C[q] -= 1
                    if self.B[q] <= -self.N[q]:
                        self.B[q] = -self.N[q] + 1
                elif self.B[q] > 0:
                    self.B[q] -= self.N[q]
                    if self.C[q] < MAX_C:
                        self.C[q] += 1
                    if self.B[q] > 0:
                        self.B[q] = 0

                if self.N[q] == RESET:
                    self.A[q] >>= 1
                    self.B[q] >>= 1
                    self.N[q] >>= 1

                self.N[q] += 1

        data = writer.to_bytes()
        trace = {
            "pred": pred,
            "err": err,
            "merr": merr,
            "k": kmap,
            "ctx_id": ctx_id_map,
        }
        return EncodeResult(bitstream_bytes=data, nbits=writer.bit_length(), trace=trace)


def encode_image(image: np.ndarray) -> EncodeResult:
    return JPEGLSRegularEncoder().encode(image)
