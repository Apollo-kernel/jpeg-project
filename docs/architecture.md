# Architecture

## Overview

The project uses a staged architecture:

```text
image / .mem input
        |
        v
Python golden model
        |
        +--> compressed golden stream
        +--> per-pixel trace arrays
        +--> CSV / JSON evidence
        |
        v
HLS encoder implementation
        |
        v
HLS C simulation testbench
        |
        v
HLS synthesis report and generated RTL
```

## Encoder Datapath

The hardware-mapped datapath is:

```text
pixel memory reader
        |
        v
neighborhood generator
        |
        v
gradient calculator / context id
        |
        v
MED predictor and context correction
        |
        v
residual mapper
        |
        v
Golomb-style encoder
        |
        v
bit packer
        |
        v
output memory writer
```

## Module Mapping

| Logical Module | Python Evidence | HLS Implementation |
|---|---|---|
| Pixel reader | `data/*.mem` | `in_pixels[y * width + x]` |
| Neighborhood generator | `*_trace.npz`, `*_trace_head.csv` | `line_prev[]`, `line_cur[]`, local `A/B/C/D` |
| Gradient calculator | context trace | `context_id_hls()` |
| Predictor | `pred` trace | `med_predictor_hls()` + `clip_u8_hls()` |
| Residual mapper | `err`, `merr` trace | `map_error_hls()` |
| Context update | trace evolution | `update_context_hls()` |
| Golomb encoder | `k`, `code_len` trace | `write_unary_hls()` + `write_bits_hls()` |
| Bit packer | `*_compressed.mem` | `write_bit_hls()` and output byte buffer |

## Causal Neighborhood

For pixel `X`, only already-known pixels are used:

```text
C  B  D
A  X
```

| Symbol | Meaning |
|---|---|
| `A` | left pixel |
| `B` | upper pixel |
| `C` | upper-left pixel |
| `D` | upper-right pixel |

For the first row or first column, missing causal neighbors are treated as zero, except `D` at the row boundary falls back to `B`.

## Context Model

The stage-2 model uses a compact 9-bin quantizer per local gradient:

```text
g1 = D - B
g2 = B - C
g3 = C - A
```

This produces:

```text
9 * 9 * 9 = 729 contexts
```

Each context stores adaptive state:

```text
A[context]
B[context]
C[context]
N[context]
```

## HLS Memory Architecture

The HLS code uses:

```text
line_prev[JPEGLS_MAX_WIDTH]
line_cur[JPEGLS_MAX_WIDTH]
```

The context memories are:

```text
ctx_A[729]
ctx_B[729]
ctx_C[729]
ctx_N[729]
```

## Bit Packing

Packing rule:

```text
MSB-first inside each byte
final partial byte zero-padded on the right
out_nbits reports the number of valid bits
```

The HLS testbench compares both output valid bit count and every output byte against the notebook-generated golden stream.

## HLS Synthesis Observations

| Item | Result |
|---|---|
| Target part | `xc7z020-clg484-1` |
| Target clock | 10.00 ns |
| Estimated clock | 8.560 ns |
| Estimated Fmax | 116.82 MHz |
| LUT utilization | 17% |
| FF utilization | 6% |
| BRAM utilization | 6% |
| DSP utilization | 1% |

The generated RTL uses AXI master interfaces for image input/output buffers and AXI-Lite for control. The design is correctness-first rather than throughput-optimized: the current architecture preserves a direct mapping from the Python golden model to HLS C++ so that the compressed bitstream can be verified exactly.

## Current Bottlenecks

The current critical paths are in:

1. Golomb parameter selection,
2. unary/remainder bit writing,
3. variable-length bit packing.

These are expected for an entropy-coded design because output length is data-dependent. Future optimization can split bit packing into a separate streaming stage and reduce the dynamic shift/comparison critical path in Golomb parameter selection.

## Verification-Oriented Implementation Strategy

The first HLS version is intentionally correctness-first. The code keeps a close mapping to the Python golden model so that the HLS C testbench can compare the exact compressed byte stream and valid bit count against Python-generated vectors.

## Pipelining and Parallelism Notes

The design uses local line buffers and context memories to avoid rereading previous pixels from external memory. The critical datapath is dominated by entropy-coding operations, especially Golomb parameter selection, unary/remainder generation, and variable-length bit packing.

Future throughput improvements can partition the encoder into these stages:

```text
pixel read / neighborhood generation
        |
        v
prediction and residual mapping
        |
        v
Golomb code generation
        |
        v
bit packing / output buffering
```

The current implementation prioritizes exact bitstream verification before deeper streaming partitioning. The included Vivado OOC script has generated IP-level post-route timing/resource/power evidence without requiring a complete board-level system.
