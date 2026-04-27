# Scope and Limitations

## Implemented Scope

| Feature | Status |
|---|---|
| 8-bit grayscale input | Implemented |
| Raster-scan pixel order | Implemented |
| Causal neighborhood A/B/C/D | Implemented |
| MED-style predictor | Implemented |
| Gradient-based context selection | Implemented |
| Adaptive context update | Implemented |
| Signed residual mapping | Implemented |
| Golomb-style entropy coding | Implemented |
| MSB-first bit packing | Implemented |
| Python golden model | Implemented |
| HLS C implementation | Implemented |
| HLS C simulation | Implemented |
| HLS synthesis | Implemented |
| Vivado synthesized timing/utilization/power reports | Implemented |

## Not Implemented

| Feature | Reason |
|---|---|
| JPEG-LS marker/header generation | Out of scope for encoder-core hardware datapath |
| Run mode | Future work |
| Near-lossless mode | Future work |
| Color component handling | Future work |
| Full ITU-T T.87 compliance | This project targets a hardware datapath subset |
| Board-level software driver | Future integration |
| Full end-to-end JPEG-LS file container | Future integration |

## Important Scope Statement

This repository implements a **JPEG-LS regular-mode inspired encoder datapath** for 8-bit grayscale lossless compression. It is not presented as a complete standards-compliant JPEG-LS file-container encoder.

The assignment evaluates hardware IP definition, design architecture, verification, synthesis evidence, and documentation. This project therefore focuses on a synthesizable encoder datapath and its verification evidence rather than full image-file container compatibility.
