# HLS Implementation

This folder contains the C++ HLS implementation corresponding to the notebook-generated Python golden model.

## Files

| File | Purpose |
|---|---|
| `jpegls_hls.hpp` | HLS constants, typedefs, and top-level function declaration |
| `jpegls_hls.cpp` | JPEG-LS regular-mode inspired HLS encoder |
| `jpegls_tb.hpp` | Testbench helper declarations |
| `jpegls_hls_tb.cpp` | Self-checking C simulation testbench |
| `run_hls.tcl` | Standard Vitis/Vivado HLS C simulation + C synthesis flow |
| `run_hls_with_cosim.tcl` | Optional full C/RTL co-simulation flow |
| `run_hls_cosim_small.tcl` | Small synthetic-test C/RTL co-simulation flow |
| `run_hls_impl.tcl` | HLS export implementation flow |

## Standard Run

From repository root:

```bash
vitis_hls -f hls/run_hls.tcl
```

Expected outputs:

```text
data/hls_csim_results.csv
reports/jpegls_encode_hls_csynth.rpt
```

## Full C/RTL Co-Simulation Option

```bash
vitis_hls -f hls/run_hls_with_cosim.tcl
```

This optional full script can take significantly longer than the standard flow because the two real images are 512x768. The committed PASS evidence uses the small synthetic-test C/RTL flow below.

## Additional Grader Evidence Scripts

### Small C/RTL Co-simulation PASS Flow

```bash
vitis_hls -f hls/run_hls_cosim_small.tcl
```

This uses `-DJPEGLS_TB_SMALL_ONLY` and `-DJPEGLS_COSIM_SMALL_DEPTH` to run C/RTL co-simulation on the six synthetic 8x8 regression tests. The committed `reports/cosim_pass_excerpt.txt` reports this flow as PASS, and the small-mode result table is stored separately in `data/hls_cosim_small_results.csv` so it does not overwrite the full 8-test `data/hls_csim_results.csv`.

### HLS Export Implementation Flow

```bash
vitis_hls -f hls/run_hls_impl.tcl
```

This attempts Vitis HLS `export_design -flow impl` to produce implementation-level IP evidence, depending on the local Vitis HLS installation.

## XML Report Parsing

After running the standard HLS flow, parse the generated C-synthesis XML report from the repository root:

```bash
python scripts/parse_csynth_pysilicon.py
```

This mirrors the course PySilicon workflow and regenerates:

```text
data/csynth_loop_info.csv
data/csynth_resource_usage.csv
```
