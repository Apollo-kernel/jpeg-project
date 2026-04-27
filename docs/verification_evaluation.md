# Verification and Evaluation

## Verification Strategy

The project uses a reference-driven verification strategy:

```text
Python golden model
        |
        v
input .mem files
compressed golden .mem files
trace files
CSV / JSON summaries
        |
        v
HLS C simulation testbench
        |
        v
HLS C synthesis report
        |
        v
Vivado synthesized timing/utilization/power reports
        |
        v
small C/RTL co-simulation PASS
        |
        v
Vivado OOC post-route timing/utilization/power PASS
```

## Python Golden Reference Evidence

The notebook:

```text
stage2_jpegls_python_implementation_all_in_one.ipynb
```

generates:

| Artifact | Purpose |
|---|---|
| `submitted_results.json` | Top-level PASS summary |
| `data/python_results.csv` | Per-image Python test table |
| `data/*.mem` | Raw grayscale input vectors |
| `data/*_compressed.mem` | Golden compressed byte streams |
| `data/*_summary.json` | Per-image metadata and valid bit count |
| `data/*_trace.npz` | Full per-pixel trace arrays |
| `data/*_trace_head.csv` | Human-readable trace preview |
| `plots/bits_per_pixel.png` | Bits-per-pixel visualization |
| `plots/compression_ratio.png` | Compression-ratio visualization |

## Current PASS Summary

| Metric | Result |
|---|---:|
| Python score | 10 / 10 |
| Python status | PASS |
| Python synthetic tests | 6 / 6 PASS |
| Python real image tests | 2 / 2 PASS |
| Python lossless decode match | true |
| HLS C simulation tests | 8 / 8 PASS |
| HLS synthesis | PASS |
| Estimated Fmax | 116.82 MHz |
| Main pixel-loop latency range | 25–591 cycles/pixel from HLS loop report |
| Explicit throughput envelope | 0.169–4.000 Mpixel/s at 100 MHz; 0.198–4.673 Mpixel/s at 116.82 MHz |
| Small C/RTL co-simulation | 6 / 6 synthetic tests PASS |
| Vivado post-route OOC implementation | PASS |
| Post-route WNS / TNS | 1.094 ns / 0.000 ns |
| Post-route timing | 0 failing endpoints; timing constraints met |

## HLS Verification Result

The HLS C simulation passed all eight Python-generated test vectors. The testbench checks both the valid compressed bit count and every compressed output byte.

| Test | Expected compressed bytes | Expected bits | Actual bits | Result |
|---|---:|---:|---:|---|
| `all_zero_8x8` | 9 | 68 | 68 | PASS |
| `constant_128_8x8` | 39 | 306 | 306 | PASS |
| `horizontal_gradient_8x8` | 25 | 196 | 196 | PASS |
| `vertical_gradient_8x8` | 29 | 225 | 225 | PASS |
| `checkerboard_8x8` | 216 | 1721 | 1721 | PASS |
| `random_8x8` | 371 | 2961 | 2961 | PASS |
| `two_macaws` | 180903 | 1447224 | 1447224 | PASS |
| `whitewater_rafting` | 244120 | 1952957 | 1952957 | PASS |

## Completed HLS Flow

The HLS flow was run with:

```bash
vitis_hls -f hls/run_hls.tcl
```

The completed sequence was:

```text
C simulation
→ C synthesis
→ RTL generation
→ synthesis report copied to reports/
```

Generated evidence:

```text
data/hls_csim_results.csv
reports/jpegls_encode_hls_csynth.rpt
reports/hls_synthesis_summary.md
```

## PySilicon-style HLS XML Parsing

In addition to the human-readable HLS `.rpt` file, the repository includes the Vitis HLS XML synthesis reports:

```text
reports/csynth.xml
reports/jpegls_encode_hls_csynth.xml
```

The XML can be parsed in the same style as the course PySilicon utilities with either:

```text
stage3_parse_hls_csynth_with_pysilicon.ipynb
```

or:

```bash
python scripts/parse_csynth_pysilicon.py
```

The parser regenerates:

| Parsed CSV | Meaning |
|---|---|
| `data/csynth_loop_info.csv` | Loop pipeline II, pipeline depth, trip-count range, and latency range |
| `data/csynth_resource_usage.csv` | HLS resource usage table extracted from `csynth.xml` |

This directly addresses the lab requirement to parse the XML synthesis report and extract loop pipeline/resource information.

## HLS Synthesis Resource Summary

| Resource | Used | Available | Utilization |
|---|---:|---:|---:|
| BRAM_18K | 18 | 280 | 6% |
| DSP | 3 | 220 | 1% |
| FF | 6619 | 106400 | 6% |
| LUT | 9337 | 53200 | 17% |
| URAM | 0 | 0 | 0% |

## Vivado Synthesized Reports

The committed package also includes synthesized Vivado reports:

| Report | Purpose |
|---|---|
| `reports/vivado_synth_timing.rpt` | Synthesized timing summary |
| `reports/vivado_synth_utilization.rpt` | Synthesized resource utilization |
| `reports/vivado_synth_power.rpt` | Synthesized power estimate |

## C/RTL Co-simulation Result

A small-only C/RTL co-simulation run was completed with:

```bash
vitis_hls -f hls/run_hls_cosim_small.tcl
```

It compiles the design and testbench with `-DJPEGLS_TB_SMALL_ONLY` and uses the small-depth m_axi wrapper configuration documented in `docs/cosim_troubleshooting.md`. The committed `reports/cosim_pass_excerpt.txt` reports:

```text
INFO: [COSIM 212-1000] *** C/RTL co-simulation finished: PASS ***
```

C/RTL co-simulation test coverage:

| Test | Size | C/RTL co-sim result |
|---|---:|---|
| `all_zero_8x8` | 8x8 | PASS |
| `constant_128_8x8` | 8x8 | PASS |
| `horizontal_gradient_8x8` | 8x8 | PASS |
| `vertical_gradient_8x8` | 8x8 | PASS |
| `checkerboard_8x8` | 8x8 | PASS |
| `random_8x8` | 8x8 | PASS |

The two 512x768 real-image tests are verified by HLS C simulation rather than C/RTL co-simulation to avoid an unnecessarily long RTL simulation run.

## Vivado Out-of-Context Implementation Result

A revised Vivado script is included:

```bash
vivado -mode batch -source scripts/vivado_impl_reports.tcl
```

The script runs synthesis and implementation in out-of-context mode. This is important because the HLS top has wide AXI-style IP interfaces; a normal full-chip top-level implementation can incorrectly treat those ports as physical package pins and fail with IO overutilization.

The committed Vivado OOC implementation reports show that placement and routing completed successfully:

| Evidence | Result |
|---|---|
| `place_design` | completed successfully |
| `route_design` | completed successfully |
| Routed design state | `Routed` |
| Post-route checkpoint | `reports/jpegls_post_route_ooc.dcp` |
| Post-route timing report | `reports/vivado_timing.rpt` |
| Post-route utilization report | `reports/vivado_utilization.rpt` |
| Post-route power report | `reports/vivado_power.rpt` |

Post-route timing summary:

| Metric | Result |
|---|---:|
| Clock period | 10.000 ns |
| WNS | 1.094 ns |
| TNS | 0.000 ns |
| Setup failing endpoints | 0 |
| Hold worst slack | 0.046 ns |
| Timing met? | Yes |

Post-route utilization summary:

| Resource | Used | Available | Utilization |
|---|---:|---:|---:|
| LUT | 4898 | 53200 | 9.2% |
| FF | 6066 | 106400 | 5.7% |
| BRAM_18K equivalent | 13 | 280 | 4.6% |
| DSP | 3 | 220 | 1.4% |

Post-route power summary:

| Metric | Result |
|---|---:|
| Total on-chip power | 0.161 W |
| Dynamic power | 0.058 W |
| Device static power | 0.104 W |

## Performance Analysis Against Goals

The initial goal for this stage was to produce a synthesizable hardware encoder that matches the Python golden model, documents latency/throughput/resource results, and can target a 100 MHz-class clock.

### Performance vs Goal Table

| Goal / Metric | Target or Requirement | Evidence | Result | Status |
|---|---|---|---|---|
| Match Python golden output | Byte-for-byte compressed stream match | `data/hls_csim_results.csv` | HLS C simulation passes 8 / 8 tests | PASS |
| Verify RTL behavior on small regression set | C/RTL co-sim PASS evidence | `reports/cosim_pass_excerpt.txt` | 6 / 6 synthetic 8x8 tests PASS | PASS |
| Synthesize to RTL | `csynth_design` completes | `reports/jpegls_encode_hls_csynth.rpt` | Verilog and VHDL generated | PASS |
| HLS target clock | 10.00 ns / 100 MHz | HLS csynth report | Estimated clock = 8.560 ns; estimated Fmax = 116.82 MHz | PASS |
| Vivado OOC post-route timing | Meet 10.00 ns clock | `reports/vivado_timing.rpt` | WNS = 1.094 ns, TNS = 0.000 ns, 0 failing endpoints | PASS |
| Approximate post-route frequency margin | Critical path faster than 10 ns | Computed from WNS | Approx. critical path = 8.906 ns, about 112.3 MHz | PASS |
| Report latency | Include HLS top-level latency and explain static bound | HLS csynth report | 15 to 2,483,040,295 cycles; 0.150 us to 24.830 sec | PASS |
| Report throughput | Include explicit throughput table | `README.md`, `data/throughput_estimates.csv` | 0.169–4.000 Mpixel/s at 100 MHz schedule envelope | PASS |
| Keep LUT usage below 25% on Zynq-7020 | Resource budget goal | HLS and Vivado reports | HLS LUT estimate = 17%; post-route LUT = 9.2% | PASS |
| Keep BRAM usage below 10% on Zynq-7020 | Resource budget goal | HLS and Vivado reports | HLS BRAM = 6%; post-route BRAM18 equivalent = 4.6% | PASS |

The HLS report gives a very large static maximum latency because the function supports variable image dimensions up to the compiled maximum width and because Golomb-style variable-length coding has data-dependent loop bounds. This is not a timing violation. Timing closure is demonstrated separately by the HLS estimated clock and Vivado post-route WNS/TNS results.

### Explicit Throughput Table

The current testbench does not log per-image RTL cycle counts, so the throughput below is a schedule-derived estimate from the HLS report rather than a measured hardware runtime. This is stated explicitly to avoid overstating the evidence.

| Throughput Item | HLS Schedule Evidence | Cycles per Unit | Throughput at 100 MHz Target | Throughput at 116.82 MHz HLS Estimated Fmax | Notes |
|---|---|---:|---:|---:|---|
| Unary bit emission loop | `write_unary_hls`, PipelineII = 1 | 1 coding bit / cycle while active | 100.00 Mbit/s | 116.82 Mbit/s | Local loop rate only. |
| Remainder bit emission loop | `write_bits_hls`, PipelineII = 1 | 1 coding bit / cycle while active | 100.00 Mbit/s | 116.82 Mbit/s | Local loop rate only. |
| Row-buffer init/copy loops | HLS pipeline loops with II = 1 | 1 pixel / cycle while active | 100.00 Mpixel/s | 116.82 Mpixel/s | Local memory loop rate. |
| Main entropy-coded pixel loop, best reported point | Inner loop iteration latency minimum | 25 cycles / pixel | 4.000 Mpixel/s | 4.673 Mpixel/s | Best HLS-reported schedule point. |
| Main entropy-coded pixel loop, conservative reported point | Inner loop iteration latency maximum | 591 cycles / pixel | 0.169 Mpixel/s | 0.198 Mpixel/s | Conservative data-dependent point. |
| End-to-end input-pixel throughput envelope | Computed from 25–591 cycles / pixel | 25–591 cycles / pixel | 0.169–4.000 Mpixel/s | 0.198–4.673 Mpixel/s | 8-bit grayscale means Mpixel/s is approximately MB/s of input pixels. |

### Real-image and C/RTL Co-simulation Coverage Boundary

The two required 512x768 real-image vectors are verified by Python and HLS C simulation. They are not claimed as full-size C/RTL co-simulation cases. The committed C/RTL co-simulation PASS evidence covers the six 8x8 synthetic regression tests. This split keeps RTL simulation time practical while still showing that generated RTL, AXI wrappers, and the self-checking post-check execute successfully.

## Evaluation Against Rubric

| Rubric Category | Current Evidence | Status |
|---|---|---|
| IP Interface Definition | `README.md`, `docs/ip_role_definition.md`, HLS function signature, HLS interface synthesis | Strong |
| IP Design | `docs/architecture.md`, `hls/jpegls_hls.cpp` | Strong for first HLS version |
| Verification | notebook PASS summary, `data/python_results.csv`, `data/hls_csim_results.csv`, HLS testbench, C/RTL co-sim PASS log | Strong; Python, HLS C simulation, and small C/RTL co-simulation pass |
| Evaluation | plots, Python compression results, HLS synthesis summary, Vivado synthesized reports, Vivado post-route OOC reports | Strong |
| Synthesis / Implementation Evidence | `reports/jpegls_encode_hls_csynth.rpt`, `reports/vivado_synth_*.rpt`, `reports/vivado_timing.rpt`, `reports/vivado_utilization.rpt`, `reports/vivado_power.rpt` | Completed HLS synthesis and Vivado OOC post-route evidence |
| Organization | cleaned repo, `.gitignore`, docs and evidence folders | Good |

## Remaining Work for a Full System Demo

The current repository already contains the main grader-facing evidence requested for this hardware IP: Python/HLS verification, HLS synthesis, small C/RTL co-simulation, and Vivado OOC post-route reports. Future work would be system-integration work rather than missing IP evidence:

- package the core as a reusable Vivado IP block,
- connect it to a Zynq processing system or DMA subsystem,
- add a streaming AXI4-Stream output mode,
- run full real-image C/RTL co-simulation if a longer RTL simulation budget is available.

## Limitations

The current implementation is:

- regular-mode inspired,
- 8-bit grayscale only,
- encoder core only,
- not a full JPEG-LS file-container encoder,
- not run-mode capable,
- not near-lossless,
- not color-component capable.
