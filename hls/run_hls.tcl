# Vitis/Vivado HLS batch script for the JPEG-LS regular-mode inspired encoder.
#
# Run from repository root:
#   vitis_hls -f hls/run_hls.tcl
# or, in newer Vitis versions:
#   vitis-run --mode hls --tcl hls/run_hls.tcl
#
# Expected outputs:
#   data/hls_csim_results.csv
#   reports/jpegls_encode_hls_csynth.rpt

open_project -reset jpegls_hls_prj
set_top jpegls_encode_hls

add_files hls/jpegls_hls.cpp -cflags "-std=c++14"
add_files hls/jpegls_hls.hpp -cflags "-std=c++14"
add_files -tb hls/jpegls_hls_tb.cpp -cflags "-std=c++14"
add_files -tb hls/jpegls_tb.hpp -cflags "-std=c++14"

# Add only the testbench data that is actually consumed by the C testbench.
# Avoid adding large/unneeded PNG, NPZ, and transient files.
set tb_data_files [concat \
    [glob -nocomplain data/*.mem] \
    [glob -nocomplain data/*_summary.json] \
    [glob -nocomplain data/*_dims.txt] \
    [glob -nocomplain data/python_results.csv] \
]

foreach f $tb_data_files {
    add_files -tb $f
}

open_solution -reset solution1
set_part xc7z020clg484-1
create_clock -period 10.0 -name default

csim_design
csynth_design

file mkdir reports
set rpt "jpegls_hls_prj/solution1/syn/report/jpegls_encode_hls_csynth.rpt"
if {[file exists $rpt]} {
    file copy -force $rpt reports/jpegls_encode_hls_csynth.rpt
}

exit
