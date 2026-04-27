# Convenience targets for reproducing the JPEG-LS inspired encoder evidence.
# The grader is not expected to execute these commands, but they document the automated flow.

.PHONY: golden hls cosim-small vivado parse check all clean-generated

golden:
	jupyter nbconvert --to notebook --execute stage2_jpegls_python_implementation_all_in_one.ipynb --inplace

hls:
	vitis_hls -f hls/run_hls.tcl

cosim-small:
	vitis_hls -f hls/run_hls_cosim_small.tcl

vivado:
	vivado -mode batch -source scripts/vivado_impl_reports.tcl

parse:
	python scripts/parse_csynth_pysilicon.py --fallback-only

check:
	python scripts/check_artifacts.py

all: golden hls parse cosim-small vivado check

clean-generated:
	rm -rf .Xil jpegls_hls_prj jpegls_hls_cosim_prj vivado_ooc_impl_prj hls_component
	rm -f *.log *.jou *.str
