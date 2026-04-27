# IP Role Definition

## IP Name

`jpegls_encode_hls`

## Role of the IP

The IP is a JPEG-LS regular-mode inspired lossless image-compression accelerator for 8-bit grayscale images. It accepts a raster-ordered pixel buffer and writes a packed variable-length compressed byte stream.

It is an encoder datapath, not a complete JPEG-LS file-container writer.

## Completed Scope

| Feature | Status | Evidence |
|---|---:|---|
| 8-bit grayscale input model | Completed | `images/`, `data/*.mem` |
| Python golden encoder/decoder | Completed | `stage2_jpegls_python_implementation_all_in_one.ipynb` |
| Lossless reconstruction check | Completed | `submitted_results.json`, `data/python_results.csv` |
| Synthetic regression images | Completed | `data/*_8x8*` |
| Real image tests | Completed | `two_macaws`, `whitewater_rafting` results |
| HLS encoder implementation | Completed | `hls/jpegls_hls.cpp`, `hls/jpegls_hls.hpp` |
| HLS C testbench | Completed | `hls/jpegls_hls_tb.cpp`, `hls/jpegls_tb.hpp` |
| HLS C simulation | Completed | `data/hls_csim_results.csv` |
| HLS synthesis | Completed | `reports/jpegls_encode_hls_csynth.rpt` |
| RTL generation | Completed by Vitis HLS | `reports/jpegls_encode_hls_csynth.rpt` |
| Vivado synthesized reports | Completed | `reports/vivado_synth_*.rpt` |
| C/RTL co-simulation | Completed | `reports/jpegls_cosim_report.md`, `reports/cosim_pass_excerpt.txt` |
| Post-route OOC implementation | Completed | `reports/vivado_implementation_summary.md`, `reports/vivado_timing.rpt` |

## Input Interface

The HLS top function is:

```cpp
void jpegls_encode_hls(
    const pixel_t *in_pixels,
    byte_t *out_bytes,
    int width,
    int height,
    int max_out_bytes,
    int *out_nbits,
    int *status
);
```

| Argument | Direction | Intended HLS Interface | Meaning |
|---|---:|---|---|
| `in_pixels` | input | `m_axi` + `s_axilite` pointer register | Row-major 8-bit grayscale pixels |
| `out_bytes` | output | `m_axi` + `s_axilite` pointer register | Packed compressed output bytes |
| `width` | input | `s_axilite` | Image width |
| `height` | input | `s_axilite` | Image height |
| `max_out_bytes` | input | `s_axilite` | Size of output byte buffer |
| `out_nbits` | output | `m_axi` + `s_axilite` pointer register | Number of valid compressed bits |
| `status` | output | `m_axi` + `s_axilite` pointer register | `0` on success, negative on error |
| return | control | `s_axilite` | Kernel start/done control |

## Synthesized Interface Summary

The HLS report/log shows that the top function was synthesized with:

| Interface | Purpose |
|---|---|
| `gmem0` / `m_axi` | input pixel memory |
| `gmem1` / `m_axi` | compressed output memory |
| `gmem2` / `m_axi` | scalar output memory for `out_nbits` and `status` |
| `control` / `s_axilite` | control registers for function arguments and start/done control |
| `ap_ctrl_hs` | block-level control protocol |

## Data Format

### Input Pixel Buffer

The input is a contiguous 8-bit grayscale raster image:

```text
in_pixels[y * width + x]
```

### Output Byte Buffer

The output stream is MSB-first packed:

```text
bit 7 -> bit 0 of out_bytes[0]
bit 7 -> bit 0 of out_bytes[1]
...
```

The final byte is zero-padded on the right if the number of valid bits is not divisible by eight. The exact valid bit count is returned through `out_nbits`.

## Status Definition

| Status | Meaning |
|---:|---|
| `0` | Success |
| `-1` | Invalid dimensions or width exceeds the compiled maximum |
| `-2` | Output byte buffer overflow |

## Mathematical Operations

For each pixel `X`, the IP uses:

```text
C  B  D
A  X
```

The datapath computes:

```text
g1 = D - B
g2 = B - C
g3 = C - A
context_id = quantize(g1, g2, g3)
Px = MED(A, B, C)
Px_corrected = clip(Px + C_context)
Err = X - Px_corrected
MErr = 2*Err      if Err >= 0
MErr = -2*Err - 1 if Err < 0
k = Golomb parameter from A_context / N_context
code = unary(MErr >> k) + low_k_bits(MErr)
```

The adaptive context state is updated after each pixel.

## Message / Control Behavior

The software or testbench provides input and output buffer addresses plus scalar arguments through the `s_axilite` control interface. The HLS block-level `ap_ctrl_hs` protocol starts the transaction and reports completion. On completion, software reads `out_nbits` and `status` to determine how many valid bits were written and whether overflow or invalid dimensions occurred.
