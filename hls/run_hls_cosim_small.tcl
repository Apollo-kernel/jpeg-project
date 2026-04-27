# hls/run_hls_cosim_small.tcl
# C/RTL co-simulation on synthetic 8x8 tests only.
#
# Run from repository root:
#   vitis_hls -f hls/run_hls_cosim_small.tcl
#
# This script intentionally defines JPEGLS_COSIM_SMALL_DEPTH for both the
# design and testbench. Without this, the C/RTL wrapper uses the large m_axi
# depths from the normal project build and may read/write beyond the small
# 8x8 testbench buffers during ENTER_WRAPC.

open_project -reset jpegls_hls_cosim_prj
set_top jpegls_encode_hls

set design_cflags "-std=c++14 -DJPEGLS_COSIM_SMALL_DEPTH"
set tb_cflags     "-std=c++14 -DJPEGLS_TB_SMALL_ONLY -DJPEGLS_COSIM_SMALL_DEPTH"

add_files hls/jpegls_hls.cpp -cflags $design_cflags
add_files hls/jpegls_hls.hpp -cflags $design_cflags

# Compile the testbench in small-only mode for faster C/RTL co-simulation.
add_files -tb hls/jpegls_hls_tb.cpp -cflags $tb_cflags
add_files -tb hls/jpegls_tb.hpp -cflags $tb_cflags

# Only add files required by the six synthetic 8x8 tests.
# Avoid copying the large real-image vectors into the co-sim project.
set small_tests {
    all_zero_8x8
    constant_128_8x8
    horizontal_gradient_8x8
    vertical_gradient_8x8
    checkerboard_8x8
    random_8x8
}

foreach name $small_tests {
    foreach suffix {".mem" "_compressed.mem" "_summary.json" "_dims.txt"} {
        set f "data/${name}${suffix}"
        if {[file exists $f]} {
            add_files -tb $f
        } else {
            puts "ERROR: missing testbench file: $f"
            exit 1
        }
    }
}

if {[file exists data/python_results.csv]} {
    add_files -tb data/python_results.csv
}

open_solution -reset solution1
set_part xc7z020clg484-1
create_clock -period 10.0 -name default

csim_design
csynth_design

# RTL co-simulation. Requires a supported Verilog simulator in the local Vitis HLS setup.
cosim_design -rtl verilog

file mkdir reports

set csynth_rpt "jpegls_hls_cosim_prj/solution1/syn/report/jpegls_encode_hls_csynth.rpt"
if {[file exists $csynth_rpt]} {
    file copy -force $csynth_rpt reports/jpegls_encode_hls_cosim_csynth.rpt
}

# Common Vitis HLS location for co-sim report/log files varies by version;
# users can copy the PASS report from jpegls_hls_cosim_prj/solution1/sim/report/.
exit
