# C/RTL Co-simulation Report

## Current Status

| Item | Result |
|---|---|
| Tool flow | Vitis HLS C/RTL co-simulation |
| Tool version | Vitis HLS 2023.2 |
| Top function | `jpegls_encode_hls` |
| RTL language | Verilog |
| Testbench mode | Small synthetic 8x8 regression mode |
| Command | `vitis_hls -f hls/run_hls_cosim_small.tcl` |
| Status in this committed package | PASS |
| Test result | 6 / 6 synthetic tests PASS |
| Main evidence | `reports/cosim_pass_excerpt.txt`, `data/hls_cosim_small_results.csv` |

## PASS Evidence

The clean package keeps the relevant PASS excerpt in `reports/cosim_pass_excerpt.txt`. It shows that C simulation, C synthesis, and C/RTL co-simulation completed successfully. The full root tool log is intentionally not committed. The C/RTL section ends with:

```text
PASS all_zero_8x8
PASS constant_128_8x8
PASS horizontal_gradient_8x8
PASS vertical_gradient_8x8
PASS checkerboard_8x8
PASS random_8x8
All HLS C simulation tests PASS.
INFO: [COSIM 212-1000] *** C/RTL co-simulation finished: PASS ***
```

## Test Set

| Test | Size | Included in small C/RTL co-sim mode | Result |
|---|---:|---:|---|
| `all_zero_8x8` | 8x8 | yes | PASS |
| `constant_128_8x8` | 8x8 | yes | PASS |
| `horizontal_gradient_8x8` | 8x8 | yes | PASS |
| `vertical_gradient_8x8` | 8x8 | yes | PASS |
| `checkerboard_8x8` | 8x8 | yes | PASS |
| `random_8x8` | 8x8 | yes | PASS |
| `two_macaws` | 512x768 | no | verified by HLS C simulation |
| `whitewater_rafting` | 512x768 | no | verified by HLS C simulation |

## Why the Small Mode Is Used

The small co-sim flow uses:

```text
-DJPEGLS_TB_SMALL_ONLY
-DJPEGLS_COSIM_SMALL_DEPTH
```

This limits the C/RTL co-simulation to six 8x8 synthetic vectors and reduces the m_axi pointer depths used by the generated co-simulation wrapper. The two real 512x768 image tests are already covered by HLS C simulation in `data/hls_csim_results.csv`; excluding them from C/RTL co-simulation keeps RTL simulation time practical while still providing RTL equivalence evidence for the core datapath.

## Previous Failure and Fix

A previous co-simulation attempt failed at the wrapper stage with `SIGSEGV` near `CodeState = ENTER_WRAPC`. That issue was caused by excessive m_axi wrapper depths for small vectors and is documented in `docs/cosim_troubleshooting.md`. The current small-depth flow fixes that issue, and the committed log now reports C/RTL co-simulation PASS.
