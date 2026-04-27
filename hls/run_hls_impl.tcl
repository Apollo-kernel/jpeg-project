# hls/run_hls_impl.tcl
# Run HLS C simulation, C synthesis, and Vivado implementation from HLS export.
#
# Run from repository root:
#   vitis_hls -f hls/run_hls_impl.tcl

open_project -reset jpegls_hls_prj
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

# Run Vivado synthesis + implementation from the HLS-generated RTL.
# Availability and exact report locations can vary by Vitis HLS version.
export_design -rtl verilog -format ip_catalog -flow impl

file mkdir reports

set csynth_rpt "jpegls_hls_prj/solution1/syn/report/jpegls_encode_hls_csynth.rpt"
if {[file exists $csynth_rpt]} {
    file copy -force $csynth_rpt reports/jpegls_encode_hls_csynth.rpt
}

exit
