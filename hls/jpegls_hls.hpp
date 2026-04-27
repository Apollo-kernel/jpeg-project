#ifndef JPEGLS_HLS_HPP
#define JPEGLS_HLS_HPP

#include <ap_int.h>

#define JPEGLS_MAX_WIDTH 2048
#define JPEGLS_NUM_CONTEXTS 729
#define JPEGLS_RESET 64
#define JPEGLS_MIN_C (-128)
#define JPEGLS_MAX_C 127

// AXI memory depths used by Vitis HLS C/RTL co-simulation.
// The regular project build keeps large depths for real image tests.
// The small C/RTL co-sim build defines JPEGLS_COSIM_SMALL_DEPTH so that
// the co-sim wrapper does not try to read/write millions of elements from
// small 8x8 testbench vectors.
#ifdef JPEGLS_COSIM_SMALL_DEPTH
#define JPEGLS_AXI_IN_DEPTH 4096
#define JPEGLS_AXI_OUT_DEPTH 16384
#else
#define JPEGLS_AXI_IN_DEPTH 4194304
#define JPEGLS_AXI_OUT_DEPTH 8388608
#endif
#define JPEGLS_AXI_SCALAR_DEPTH 1


typedef ap_uint<8> pixel_t;
typedef ap_uint<8> byte_t;
typedef ap_int<16> sample_diff_t;
typedef ap_uint<16> dim_t;

// Top-level HLS encoder.
// Input: row-major 8-bit grayscale pixels.
// Output: MSB-first packed variable-length compressed byte stream.
extern "C" void jpegls_encode_hls(
    const pixel_t *in_pixels,
    byte_t *out_bytes,
    int width,
    int height,
    int max_out_bytes,
    int *out_nbits,
    int *status
);

#endif  // JPEGLS_HLS_HPP
