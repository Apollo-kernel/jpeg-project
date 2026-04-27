# Reports Directory

This directory contains committed verification, synthesis, C/RTL co-simulation, and Vivado out-of-context implementation evidence for the JPEG-LS regular-mode inspired encoder IP.

## Committed Evidence

| File | Purpose |
|---|---|
| `jpegls_encode_hls_csynth.rpt` | Vitis HLS C synthesis report |
| `jpegls_encode_hls_csynth.xml` | Vitis HLS top-function XML synthesis report |
| `csynth.xml` | Vitis HLS XML synthesis report with module-level loop/resource information |
| `hls_synthesis_summary.md` | Human-readable HLS synthesis summary |
| `jpegls_cosim_report.md` | Human-readable C/RTL co-simulation PASS summary |
| `cosim_pass_excerpt.txt` | Extracted C/RTL PASS lines from the original Vitis HLS batch log |
| `jpegls_encode_hls_cosim_csynth.rpt` | HLS synthesis report from the small C/RTL co-sim project |
| `vivado_synth_timing.rpt` | Vivado synthesized timing summary |
| `vivado_synth_utilization.rpt` | Vivado synthesized utilization report |
| `vivado_synth_power.rpt` | Vivado synthesized power estimate |
| `vivado_timing.rpt` | Vivado post-route OOC timing summary |
| `vivado_utilization.rpt` | Vivado post-route OOC utilization report |
| `vivado_power.rpt` | Vivado post-route OOC power estimate |
| `jpegls_post_route_ooc.dcp` | Vivado post-route OOC checkpoint |
| `vivado_implementation_summary.md` | Human-readable Vivado OOC implementation PASS summary |
| `vivado_ooc_pass_excerpt.txt` | Extracted OOC place/route PASS lines from the original Vivado batch log |

## Key Results

| Evidence | Result |
|---|---|
| HLS C simulation | 8 / 8 tests PASS |
| HLS synthesis | PASS; estimated clock 8.560 ns |
| Small C/RTL co-simulation | 6 / 6 synthetic tests PASS |
| Vivado OOC implementation | `place_design` and `route_design` completed successfully |
| Post-route timing | WNS 1.094 ns, TNS 0.000 ns, 0 failing endpoints |
| Post-route power | Total 0.161 W |

## Regeneration Commands

From the repository root:

```bash
vitis_hls -f hls/run_hls.tcl
vitis_hls -f hls/run_hls_cosim_small.tcl
vivado -mode batch -source scripts/vivado_impl_reports.tcl
```

## PySilicon-style XML Parsing

The HLS XML report can be parsed with:

```bash
python scripts/parse_csynth_pysilicon.py
```

This regenerates:

```text
data/csynth_loop_info.csv
data/csynth_resource_usage.csv
```

The script first tries the course PySilicon parser (`pysilicon.utils.csynthparse.CsynthParser`) and falls back to a local XML parser if PySilicon is not installed.

## C/RTL Co-simulation Scope

The committed C/RTL co-simulation PASS is real and is explained in `docs/cosim_status.md`. It covers the 6/6 small synthetic 8x8 regression mode; the two 512x768 real images are covered by HLS C simulation.
