# Grader Checklist

This page maps the assignment rubric directly to the files the LLM grader should inspect.

## 1. IP Interface Definition

| Requirement | Evidence |
|---|---|
| IP role clearly defined | `README.md`, `docs/ip_role_definition.md` |
| Mathematical operations specified | `README.md`, `docs/architecture.md`, `docs/ip_role_definition.md` |
| Data flow specified | `docs/architecture.md` |
| Processing-system / testbench messages defined | `docs/ip_role_definition.md`, `hls/jpegls_hls_tb.cpp` |
| HLS interface defined | `hls/jpegls_hls.cpp`, `reports/jpegls_encode_hls_csynth.rpt` |

Key interface summary:

- Top function: `jpegls_encode_hls`.
- Input: row-major 8-bit grayscale pixel buffer through `m_axi`.
- Output: MSB-first packed compressed byte stream through `m_axi`.
- Control: scalar arguments and start/done through `s_axilite` / `ap_ctrl_hs`.
- Completion status: `out_nbits` gives valid bit count; `status=0` means success.

## 2. IP Design

| Requirement | Evidence |
|---|---|
| Architecture mapped out | `docs/architecture.md` |
| Logical module partitioning | `docs/architecture.md`, `hls/jpegls_hls.cpp` |
| Pipelining and parallelism strategy | `docs/architecture.md`, `reports/hls_synthesis_summary.md`, `data/csynth_loop_info.csv` |
| Resource strategy | `hls/jpegls_hls.cpp`, `reports/hls_synthesis_summary.md`, `data/csynth_resource_usage.csv` |

The design uses line buffers for causal neighborhood reuse, local BRAM-backed context memories, inlined arithmetic helpers for the predictor/context path, and a separate variable-length bit-writing path. This version prioritizes exact bitstream equivalence with the Python golden model while still meeting the 10 ns post-route out-of-context timing goal.

## 3. Verification and Evaluation

| Requirement | Evidence |
|---|---|
| Python golden model | `stage2_jpegls_python_implementation_all_in_one.ipynb`, `data/python_results.csv` |
| HLS C simulation | `data/hls_csim_results.csv`, `reports/hls_synthesis_summary.md` |
| HLS synthesis | `reports/jpegls_encode_hls_csynth.rpt`, `reports/csynth.xml` |
| PySilicon-style report parsing | `stage3_parse_hls_csynth_with_pysilicon.ipynb`, `scripts/parse_csynth_pysilicon.py`, `data/csynth_loop_info.csv`, `data/csynth_resource_usage.csv` |
| C/RTL co-simulation | `docs/cosim_status.md`, `reports/jpegls_cosim_report.md`, `reports/cosim_pass_excerpt.txt`, `data/hls_cosim_small_results.csv` |
| Vivado post-route implementation | `reports/vivado_implementation_summary.md`, `reports/vivado_timing.rpt`, `reports/vivado_utilization.rpt`, `reports/vivado_power.rpt` |
| Goal comparison | `README.md`, `docs/verification_evaluation.md`, `data/performance_vs_goal.csv` |
| Explicit throughput reporting | `README.md`, `docs/verification_evaluation.md`, `data/throughput_estimates.csv` |

Main results:

| Check | Result |
|---|---:|
| Python golden model | 8 / 8 tests PASS |
| HLS C simulation | 8 / 8 tests PASS |
| Small C/RTL co-simulation | 6 / 6 synthetic tests PASS |
| HLS estimated clock | 8.560 ns |
| HLS estimated Fmax | 116.82 MHz |
| Explicit throughput estimate | 0.169–4.000 Mpixel/s at 100 MHz; 0.198–4.673 Mpixel/s at 116.82 MHz |
| Vivado post-route WNS / TNS | 1.094 ns / 0.000 ns |
| Vivado post-route timing | Met |
| Post-route LUT / FF / BRAM18 / DSP | 4898 / 6066 / 13 / 3 |
| Post-route total power | 0.161 W |

## 4. Organization and Documentation

| Requirement | Evidence |
|---|---|
| AI-readable Markdown documentation | `README.md`, `docs/*.md`, `reports/*.md` |
| Clean repo | `.gitignore`, absence of `.Xil/`, HLS project directories, Vivado project directories, root `*.log`, root `*.jou` |
| Automated methodology | `Makefile`, `hls/run_hls.tcl`, `hls/run_hls_cosim_small.tcl`, `scripts/vivado_impl_reports.tcl`, `scripts/check_artifacts.py` |
| Reader can follow design to implementation | `README.md` evidence map and this checklist |

The clean grading package intentionally excludes bulky generated tool projects and full root logs. The relevant PASS lines are preserved in `reports/cosim_pass_excerpt.txt` and `reports/vivado_ooc_pass_excerpt.txt`, while full synthesis/implementation reports are preserved under `reports/`.

## Recommended Submission Note

```text
Repository URL: <your GitHub URL>

Please start with README.md and docs/grader_checklist.md. This project implements a JPEG-LS regular-mode inspired 8-bit grayscale lossless encoder datapath. The IP interface is documented in docs/ip_role_definition.md. The architecture and module partitioning are documented in docs/architecture.md. Verification evidence includes Python golden-model results, HLS C simulation for 8/8 tests, Vitis HLS synthesis reports and XML parsing, explicit latency/throughput/performance-vs-goal tables, small C/RTL co-simulation PASS evidence for 6/6 synthetic tests, and Vivado out-of-context post-route timing/utilization/power reports. The two real images are verified by Python and HLS C simulation, while C/RTL co-sim coverage is intentionally limited to small synthetic vectors. The clean repository excludes generated Vitis/Vivado project directories and root log/journal files; report summaries and PASS excerpts are committed under reports/.
```


## Direct Answer on C/RTL Co-simulation

The C/RTL co-simulation PASS is real and documented in `docs/cosim_status.md`. The final Vitis HLS message is preserved in `reports/cosim_pass_excerpt.txt`: `INFO: [COSIM 212-1000] *** C/RTL co-simulation finished: PASS ***`.
