# Reproducibility and Automation

The grader is not expected to execute the repository, but the methodology is automated and documented.

## One-command Convenience Targets

```bash
make golden        # regenerate Python golden vectors and plots
make hls           # run HLS C simulation and C synthesis
make parse         # parse csynth.xml into CSV tables
make cosim-small   # run small synthetic C/RTL co-simulation
make vivado        # run Vivado out-of-context implementation reports
make check         # check committed evidence consistency
```

Equivalent direct commands are shown below.

## Python Golden Model

```bash
jupyter nbconvert --to notebook --execute stage2_jpegls_python_implementation_all_in_one.ipynb --inplace
```

Outputs include `submitted_results.json`, `data/python_results.csv`, `.mem` vectors, compressed golden streams, per-pixel trace previews, and plots.

## Vitis HLS C Simulation and Synthesis

```bash
vitis_hls -f hls/run_hls.tcl
```

Outputs include:

```text
data/hls_csim_results.csv
reports/jpegls_encode_hls_csynth.rpt
reports/jpegls_encode_hls_csynth.xml
reports/csynth.xml
reports/hls_synthesis_summary.md
```

## PySilicon-style XML Parsing

```bash
python scripts/parse_csynth_pysilicon.py --fallback-only
```

The script attempts to mirror the course PySilicon parser workflow and falls back to a local XML parser when PySilicon is unavailable. Outputs:

```text
data/csynth_loop_info.csv
data/csynth_resource_usage.csv
```

## Small C/RTL Co-simulation

```bash
vitis_hls -f hls/run_hls_cosim_small.tcl
```

The small mode uses only the six 8x8 synthetic regression tests and writes:

```text
data/hls_cosim_small_results.csv
```

The PASS evidence excerpt is committed as:

```text
reports/cosim_pass_excerpt.txt
```

The two 512x768 real images are verified in HLS C simulation to avoid unnecessarily long RTL simulation time.

## Vivado Out-of-Context Implementation

```bash
vivado -mode batch -source scripts/vivado_impl_reports.tcl
```

Outputs include synthesized and post-route timing/utilization/power reports under `reports/`. The relevant PASS excerpt from the original batch log is committed as:

```text
reports/vivado_ooc_pass_excerpt.txt
```

## Clean Repository Policy

The final grading repository should commit source, scripts, Markdown documentation, CSV summaries, plots, images, and report files. It should not commit full generated HLS/Vivado project folders or root log/journal files.

Excluded by `.gitignore`:

```text
.Xil/
jpegls_hls_prj/
jpegls_hls_cosim_prj/
vivado_ooc_impl_prj/
*.log
*.jou
__MACOSX/
```
