# C/RTL Co-simulation Status

## Direct Answer

Yes. This repository contains evidence of a real Vitis HLS C/RTL co-simulation run that completed successfully.

The committed PASS excerpt is:

```text
reports/cosim_pass_excerpt.txt
```

The excerpt comes from the original Vitis HLS 2023.2 batch log. It shows all of the following steps happened in the tool flow:

1. XSIM was selected for RTL simulation.
2. The generated Verilog RTL simulation ran through 6 / 6 transactions.
3. The post-checking C testbench re-read the RTL results.
4. The final Vitis HLS message was:

```text
INFO: [COSIM 212-1000] *** C/RTL co-simulation finished: PASS ***
```

## Scope of the Co-simulation

The C/RTL co-simulation was run in the intentionally small synthetic regression mode:

```text
vitis_hls -f hls/run_hls_cosim_small.tcl
```

That mode verifies the RTL against six 8x8 synthetic vectors:

| Test | Result |
|---|---|
| `all_zero_8x8` | PASS |
| `constant_128_8x8` | PASS |
| `horizontal_gradient_8x8` | PASS |
| `vertical_gradient_8x8` | PASS |
| `checkerboard_8x8` | PASS |
| `random_8x8` | PASS |

The two 512x768 real images were verified by the Python golden model and the HLS C simulation flow, not by full-size C/RTL co-simulation. This is documented explicitly to avoid overstating the evidence: real images are claimed as Python + HLS C simulation PASS cases, while the committed C/RTL PASS claim is limited to the six small synthetic vectors.

## Why This Still Supports the Hardware Verification Claim

The small C/RTL co-sim proves that the synthesized RTL, generated AXI wrappers, and self-checking C post-check can execute successfully and match the golden compressed byte streams for representative datapath cases. The full 8-vector HLS C simulation covers both synthetic and real images and validates the algorithmic implementation against the Python golden reference.

The combined evidence is therefore:

| Verification layer | Coverage | Evidence |
|---|---|---|
| Python golden reference | 8 / 8, including two real images | `data/python_results.csv` |
| HLS C simulation | 8 / 8, including two real images | `data/hls_csim_results.csv` |
| C/RTL co-simulation | 6 / 6 small synthetic tests | `data/hls_cosim_small_results.csv`, `reports/cosim_pass_excerpt.txt` |
| HLS synthesis | PASS | `reports/jpegls_encode_hls_csynth.rpt`, `reports/csynth.xml` |
| Vivado OOC place/route | PASS, timing met | `reports/vivado_implementation_summary.md`, `reports/vivado_timing.rpt` |
