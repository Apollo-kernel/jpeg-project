#include "jpegls_hls.hpp"

static int clip_u8_hls(int v) {
#pragma HLS INLINE
    if (v < 0) return 0;
    if (v > 255) return 255;
    return v;
}

static int med_predictor_hls(int a, int b, int c) {
#pragma HLS INLINE
    if (c >= ((a > b) ? a : b)) {
        return (a < b) ? a : b;
    }
    if (c <= ((a < b) ? a : b)) {
        return (a > b) ? a : b;
    }
    return a + b - c;
}

static int quantize_gradient_hls(int g) {
#pragma HLS INLINE
    if (g <= -128) return -4;
    if (g <=  -64) return -3;
    if (g <=  -32) return -2;
    if (g <=   -8) return -1;
    if (g <      8) return  0;
    if (g <     32) return  1;
    if (g <     64) return  2;
    if (g <    128) return  3;
    return 4;
}

static int context_id_hls(int a, int b, int c, int d) {
#pragma HLS INLINE
    const int g1 = d - b;
    const int g2 = b - c;
    const int g3 = c - a;

    const int q1 = quantize_gradient_hls(g1);
    const int q2 = quantize_gradient_hls(g2);
    const int q3 = quantize_gradient_hls(g3);

    return (q1 + 4) * 81 + (q2 + 4) * 9 + (q3 + 4);
}

static int map_error_hls(int err) {
#pragma HLS INLINE
    return (err >= 0) ? (2 * err) : (-2 * err - 1);
}

static int golomb_k_hls(int A, int N) {
#pragma HLS INLINE
    int k = 0;
    while ((N << k) < A) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=16
        k++;
    }
    return k;
}

static void update_context_hls(
    int q,
    int err,
    int ctx_A[JPEGLS_NUM_CONTEXTS],
    int ctx_B[JPEGLS_NUM_CONTEXTS],
    int ctx_C[JPEGLS_NUM_CONTEXTS],
    int ctx_N[JPEGLS_NUM_CONTEXTS]
) {
#pragma HLS INLINE
    ctx_B[q] += err;
    ctx_A[q] += (err >= 0) ? err : -err;

    if (ctx_B[q] <= -ctx_N[q]) {
        ctx_B[q] += ctx_N[q];
        if (ctx_C[q] > JPEGLS_MIN_C) {
            ctx_C[q] -= 1;
        }
        if (ctx_B[q] <= -ctx_N[q]) {
            ctx_B[q] = -ctx_N[q] + 1;
        }
    } else if (ctx_B[q] > 0) {
        ctx_B[q] -= ctx_N[q];
        if (ctx_C[q] < JPEGLS_MAX_C) {
            ctx_C[q] += 1;
        }
        if (ctx_B[q] > 0) {
            ctx_B[q] = 0;
        }
    }

    if (ctx_N[q] == JPEGLS_RESET) {
        ctx_A[q] >>= 1;
        ctx_B[q] >>= 1;
        ctx_N[q] >>= 1;
    }

    ctx_N[q] += 1;
}

static void write_bit_hls(
    byte_t *out_bytes,
    int max_out_bytes,
    int &out_idx,
    ap_uint<8> &cur_byte,
    int &nbits_cur,
    int &total_bits,
    int bit,
    int &overflow
) {
#pragma HLS INLINE
    if (overflow) return;

    cur_byte = (ap_uint<8>)((cur_byte << 1) | (bit & 1));
    nbits_cur++;
    total_bits++;

    if (nbits_cur == 8) {
        if (out_idx >= max_out_bytes) {
            overflow = 1;
            return;
        }
        out_bytes[out_idx] = cur_byte;
        out_idx++;
        cur_byte = 0;
        nbits_cur = 0;
    }
}

static void write_bits_hls(
    byte_t *out_bytes,
    int max_out_bytes,
    int &out_idx,
    ap_uint<8> &cur_byte,
    int &nbits_cur,
    int &total_bits,
    int value,
    int nbits,
    int &overflow
) {
#pragma HLS INLINE off
    for (int i = nbits - 1; i >= 0; --i) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=16
        write_bit_hls(out_bytes, max_out_bytes, out_idx, cur_byte,
                      nbits_cur, total_bits, (value >> i) & 1, overflow);
    }
}

static void write_unary_hls(
    byte_t *out_bytes,
    int max_out_bytes,
    int &out_idx,
    ap_uint<8> &cur_byte,
    int &nbits_cur,
    int &total_bits,
    int q,
    int &overflow
) {
#pragma HLS INLINE off
    for (int i = 0; i < q; ++i) {
#pragma HLS LOOP_TRIPCOUNT min=0 max=1024
        write_bit_hls(out_bytes, max_out_bytes, out_idx, cur_byte,
                      nbits_cur, total_bits, 0, overflow);
    }
    write_bit_hls(out_bytes, max_out_bytes, out_idx, cur_byte,
                  nbits_cur, total_bits, 1, overflow);
}

extern "C" void jpegls_encode_hls(
    const pixel_t *in_pixels,
    byte_t *out_bytes,
    int width,
    int height,
    int max_out_bytes,
    int *out_nbits,
    int *status
) {
#pragma HLS INTERFACE m_axi     port=in_pixels    offset=slave bundle=gmem0 depth=JPEGLS_AXI_IN_DEPTH
#pragma HLS INTERFACE m_axi     port=out_bytes    offset=slave bundle=gmem1 depth=JPEGLS_AXI_OUT_DEPTH
#pragma HLS INTERFACE m_axi     port=out_nbits    offset=slave bundle=gmem2 depth=JPEGLS_AXI_SCALAR_DEPTH
#pragma HLS INTERFACE m_axi     port=status       offset=slave bundle=gmem2 depth=JPEGLS_AXI_SCALAR_DEPTH

#pragma HLS INTERFACE s_axilite port=in_pixels    bundle=control
#pragma HLS INTERFACE s_axilite port=out_bytes    bundle=control
#pragma HLS INTERFACE s_axilite port=width        bundle=control
#pragma HLS INTERFACE s_axilite port=height       bundle=control
#pragma HLS INTERFACE s_axilite port=max_out_bytes bundle=control
#pragma HLS INTERFACE s_axilite port=out_nbits    bundle=control
#pragma HLS INTERFACE s_axilite port=status       bundle=control
#pragma HLS INTERFACE s_axilite port=return       bundle=control

    if (out_nbits) {
        out_nbits[0] = 0;
    }
    if (status) {
        status[0] = 0;
    }

    if (width <= 0 || height <= 0 || width > JPEGLS_MAX_WIDTH || max_out_bytes <= 0) {
        if (status) status[0] = -1;
        return;
    }

    pixel_t line_prev[JPEGLS_MAX_WIDTH];
    pixel_t line_cur[JPEGLS_MAX_WIDTH];

    int ctx_A[JPEGLS_NUM_CONTEXTS];
    int ctx_B[JPEGLS_NUM_CONTEXTS];
    int ctx_C[JPEGLS_NUM_CONTEXTS];
    int ctx_N[JPEGLS_NUM_CONTEXTS];

#pragma HLS BIND_STORAGE variable=line_prev type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=line_cur  type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=ctx_A type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=ctx_B type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=ctx_C type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=ctx_N type=ram_1p impl=bram

    // Initialize row buffers.
    for (int x = 0; x < JPEGLS_MAX_WIDTH; ++x) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=2048
        line_prev[x] = 0;
        line_cur[x] = 0;
    }

    // Initialize context state to match the Python notebook model.
    for (int i = 0; i < JPEGLS_NUM_CONTEXTS; ++i) {
#pragma HLS LOOP_TRIPCOUNT min=729 max=729
        ctx_A[i] = 4;
        ctx_B[i] = 0;
        ctx_C[i] = 0;
        ctx_N[i] = 1;
    }

    int out_idx = 0;
    ap_uint<8> cur_byte = 0;
    int nbits_cur = 0;
    int total_bits = 0;
    int overflow = 0;

    for (int y = 0; y < height; ++y) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=2048
        for (int x = 0; x < width; ++x) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=2048
            const int idx = y * width + x;
            const int X = (int)in_pixels[idx];

            const int A = (x > 0) ? (int)line_cur[x - 1] : 0;
            const int B = (int)line_prev[x];
            const int C = (x > 0) ? (int)line_prev[x - 1] : 0;
            const int D = (x + 1 < width) ? (int)line_prev[x + 1] : B;

            line_cur[x] = (pixel_t)X;

            const int q = context_id_hls(A, B, C, D);
            const int px0 = med_predictor_hls(A, B, C);
            const int px = clip_u8_hls(px0 + ctx_C[q]);

            const int err = X - px;
            const int merr = map_error_hls(err);
            const int k = golomb_k_hls(ctx_A[q], ctx_N[q]);

            const int unary_q = merr >> k;
            const int rem = (k > 0) ? (merr & ((1 << k) - 1)) : 0;

            write_unary_hls(out_bytes, max_out_bytes, out_idx, cur_byte,
                            nbits_cur, total_bits, unary_q, overflow);
            if (k > 0) {
                write_bits_hls(out_bytes, max_out_bytes, out_idx, cur_byte,
                               nbits_cur, total_bits, rem, k, overflow);
            }

            update_context_hls(q, err, ctx_A, ctx_B, ctx_C, ctx_N);
        }

        // Move current row into previous-row buffer.
        for (int x = 0; x < width; ++x) {
#pragma HLS LOOP_TRIPCOUNT min=1 max=2048
            line_prev[x] = line_cur[x];
        }
    }

    // Flush final partial byte with right-side zero padding.
    if (!overflow && nbits_cur > 0) {
        if (out_idx >= max_out_bytes) {
            overflow = 1;
        } else {
            out_bytes[out_idx] = (byte_t)(cur_byte << (8 - nbits_cur));
            out_idx++;
        }
    }

    if (out_nbits) {
        out_nbits[0] = total_bits;
    }
    if (status) {
        status[0] = overflow ? -2 : 0;
    }
}
