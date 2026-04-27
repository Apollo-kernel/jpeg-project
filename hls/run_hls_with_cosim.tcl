# Optional extended HLS flow with C/RTL co-simulation.
#
# This script is NOT required for the current submitted evidence package.
# It is provided as a future extension if C/RTL co-simulation support is needed.
#
# Run from repository root:
#   vitis_hls -f hls/run_hls_with_cosim.tcl
#
# Note: C/RTL co-simulation can take significantly longer than C simulation,
# especially for the two 512x768 real-image tests.

open_project -reset jpegls_hls_prj_cosim
set_top jpegls_encode_hls

add_files hls/jpegls_hls.cpp -cflags "-std=c++14"
add_files hls/jpegls_hls.hpp -cflags "-std=c++14"
add_files -tb hls/jpegls_hls_tb.cpp -cflags "-std=c++14"
add_files -tb hls/jpegls_tb.hpp -cflags "-std=c++14"

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
cosim_design -rtl verilog

file mkdir reports
set rpt "jpegls_hls_prj_cosim/solution1/syn/report/jpegls_encode_hls_csynth.rpt"
if {[file exists $rpt]} {
    file copy -force $rpt reports/jpegls_encode_hls_csynth.rpt
}

exit
