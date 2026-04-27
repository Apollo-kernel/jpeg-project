# HLS Synthesis Summary

## Tool and Target

| Item | Result |
|---|---|
| Tool | Vitis HLS 2023.2 |
| Top function | `jpegls_encode_hls` |
| Target device | `xc7z020-clg484-1` |
| Target clock | 10.00 ns |
| Estimated clock | 8.560 ns |
| Estimated Fmax | 116.82 MHz |
| Full report | `jpegls_encode_hls_csynth.rpt` |

## C Simulation

| Test | Size | Expected Bits | Actual Bits | Result |
|---|---:|---:|---:|---|
| `all_zero_8x8` | 8×8 | 68 | 68 | PASS |
| `constant_128_8x8` | 8×8 | 306 | 306 | PASS |
| `horizontal_gradient_8x8` | 8×8 | 196 | 196 | PASS |
| `vertical_gradient_8x8` | 8×8 | 225 | 225 | PASS |
| `checkerboard_8x8` | 8×8 | 1721 | 1721 | PASS |
| `random_8x8` | 8×8 | 2961 | 2961 | PASS |
| `two_macaws` | 512×768 | 1447224 | 1447224 | PASS |
| `whitewater_rafting` | 512×768 | 1952957 | 1952957 | PASS |

## Resource Utilization

| Resource | Used | Available | Utilization |
|---|---:|---:|---:|
| BRAM_18K | 18 | 280 | 6% |
| DSP | 3 | 220 | 1% |
| FF | 6619 | 106400 | 6% |
| LUT | 9337 | 53200 | 17% |
| URAM | 0 | 0 | 0% |

## Parsed XML Report Tables

The committed XML reports are:

```text
reports/csynth.xml
reports/jpegls_encode_hls_csynth.xml
```

They can be regenerated and parsed with:

```bash
python scripts/parse_csynth_pysilicon.py
```

The parser writes:

```text
data/csynth_loop_info.csv
data/csynth_resource_usage.csv
```

Selected loop-pipeline entries:

| Loop | PipelineII | PipelineDepth | LatencyMin | LatencyMax |
|---|---:|---:|---:|---:|
|jpegls_encode_hls_Pipeline_VITIS_LOOP_220_1:VITIS_LOOP_220_1|1|1|2048|2048|
|jpegls_encode_hls_Pipeline_VITIS_LOOP_227_2:VITIS_LOOP_227_2|1|1|729|729|
|jpegls_encode_hls_Pipeline_VITIS_LOOP_55_1:VITIS_LOOP_55_1|1|2|0|16|
|write_unary_hls_Pipeline_VITIS_LOOP_160_1:VITIS_LOOP_160_1|1|8|0|517|
|write_bits_hls:VITIS_LOOP_142_1|1|8|0|22|
|jpegls_encode_hls_Pipeline_VITIS_LOOP_277_5:VITIS_LOOP_277_5|1|2|1|2048|

## Performance and Latency Notes

The HLS synthesis report gives a large static maximum latency because image size and entropy-coded output length are data-dependent. The functional submission uses fixed Python-generated test vectors for HLS C simulation.

| Metric | Result |
|---|---:|
| Target clock | 10.00 ns / 100 MHz |
| HLS estimated clock | 8.560 ns |
| HLS estimated Fmax | 116.82 MHz |
| Top-level latency range | 15 to 2,483,040,295 cycles |
| Top-level absolute latency range | 0.150 us to 24.830 sec |
| Inner pixel-loop iteration latency | 25–591 cycles / pixel |
| Input-pixel throughput envelope at 100 MHz | 0.169–4.000 Mpixel/s |
| Input-pixel throughput envelope at 116.82 MHz | 0.198–4.673 Mpixel/s |

The throughput envelope is computed from the HLS-reported inner pixel-loop latency range. It is a schedule-derived estimate, not a measured per-image RTL wall-clock result. The current goal is correctness-first hardware generation:

- match the Python golden compressed output,
- synthesize to RTL,
- target a 100 MHz-class clock,
- keep resource usage modest on Zynq-7020,
- document latency, throughput, and resource use clearly enough for grader inspection.
