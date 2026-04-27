# C/RTL Co-simulation Troubleshooting

## Current Status

The wrapper-depth problem described below has been fixed in the current small C/RTL co-simulation flow. The committed `reports/cosim_pass_excerpt.txt` now reports `C/RTL co-simulation finished: PASS` for the six synthetic 8x8 tests.

## Observed Previous Failure

A previous run of `vitis_hls -f hls/run_hls_cosim_small.tcl` failed during the C/RTL co-simulation wrapper stage with a `SIGSEGV` at `CodeState = ENTER_WRAPC`.

The HLS C simulation part passed all six synthetic 8x8 tests before the co-simulation wrapper failed. This means the C testbench and the C++ HLS model were functionally correct for the small regression set, but the generated co-simulation wrapper could not safely marshal the m_axi pointer arguments.

## Root Cause

The normal HLS top-level interface used large m_axi depths:

| Interface | Normal depth |
|---|---:|
| `in_pixels` | 4,194,304 |
| `out_bytes` | 8,388,608 |

During C/RTL co-simulation, Vitis HLS uses the declared pointer depth when it generates transaction files for m_axi interfaces. If the testbench passes a small vector such as a 64-pixel 8x8 image, but the wrapper expects to dump millions of elements, the wrapper can read or write beyond the allocated vector and crash before RTL simulation starts.

## Fix Applied

The small co-simulation flow now defines:

```text
-DJPEGLS_COSIM_SMALL_DEPTH
```

for both the design and the testbench. This changes the m_axi depths only for the small C/RTL co-sim project:

| Interface | Small co-sim depth |
|---|---:|
| `in_pixels` | 4,096 |
| `out_bytes` | 16,384 |

The testbench also pads its input and output vectors to these depths before calling `jpegls_encode_hls`.

## Files Changed

| File | Change |
|---|---|
| `hls/jpegls_hls.hpp` | Adds depth macros for normal vs small co-sim builds |
| `hls/jpegls_hls.cpp` | Uses depth macros in HLS interface pragmas |
| `hls/jpegls_hls_tb.cpp` | Pads C/RTL co-sim buffers to match m_axi depths |
| `hls/run_hls_cosim_small.tcl` | Defines `JPEGLS_COSIM_SMALL_DEPTH` and only adds small test vectors |

## Command

```bash
vitis_hls -f hls/run_hls_cosim_small.tcl
```

The current committed package includes the successful PASS log evidence in `reports/cosim_pass_excerpt.txt` and summarizes it in `reports/jpegls_cosim_report.md`.
