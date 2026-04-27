# Vivado Out-of-Context Implementation Summary

## Current Status

| Item | Result |
|---|---|
| Tool flow | Vivado out-of-context IP implementation |
| Tool version | Vivado 2023.2 |
| Top module | `jpegls_encode_hls` |
| Target device | `xc7z020clg484-1` |
| Design state | Routed |
| `place_design` | completed successfully |
| `route_design` | completed successfully |
| Timing constraints | met |
| Post-route checkpoint | `reports/jpegls_post_route_ooc.dcp` |

The out-of-context flow is the correct implementation mode for this HLS IP because the top-level ports are AXI-style IP interfaces. A normal board-level implementation can incorrectly treat the wide AXI signals as package pins and produce IO overutilization errors. In the current committed run, the OOC implementation completes placement, routing, timing analysis, utilization reporting, power reporting, and checkpoint generation.

## Command Used

Run from the repository root after HLS synthesis:

```bash
vitis_hls -f hls/run_hls.tcl
vivado -mode batch -source scripts/vivado_impl_reports.tcl
```

## Committed Post-route Evidence

| Report | Meaning |
|---|---|
| `reports/vivado_timing.rpt` | Post-route out-of-context timing summary |
| `reports/vivado_utilization.rpt` | Post-route out-of-context resource utilization |
| `reports/vivado_power.rpt` | Post-route out-of-context power estimate |
| `reports/jpegls_post_route_ooc.dcp` | Post-route out-of-context checkpoint |

## Vivado Log Summary

The clean package keeps the relevant Vivado PASS excerpt in `reports/vivado_ooc_pass_excerpt.txt`. It includes these successful implementation messages:

```text
place_design completed successfully
route_design completed successfully
INFO: [Route 35-16] Router Completed Successfully
Verification completed successfully
```

The earlier full-chip-style IO overutilization problem is not present in this OOC implementation result.

## Timing Summary

From `reports/vivado_timing.rpt`:

| Metric | Result |
|---|---:|
| Clock period | 10.000 ns |
| WNS | 1.094 ns |
| TNS | 0.000 ns |
| Setup failing endpoints | 0 |
| Hold worst slack | 0.046 ns |
| Hold total violation | 0.000 ns |
| Pulse-width worst slack | 4.020 ns |
| Timing met? | Yes |

The report states:

```text
All user specified timing constraints are met.
```

## Utilization Summary

From `reports/vivado_utilization.rpt` for the routed OOC design:

| Resource | Used | Available | Utilization |
|---|---:|---:|---:|
| LUT | 4898 | 53200 | 9.2% |
| FF | 6066 | 106400 | 5.7% |
| RAMB36 | 4 | 140 | 2.9% |
| RAMB18 | 5 | 280 | 1.8% |
| BRAM_18K equivalent | 13 | 280 | 4.6% |
| DSP | 3 | 220 | 1.4% |

## Power Summary

From `reports/vivado_power.rpt`:

| Metric | Result |
|---|---:|
| Total on-chip power | 0.161 W |
| Dynamic power | 0.058 W |
| Device static power | 0.104 W |
| Junction temperature | 26.9 C |
| Confidence level | Medium |

## Interpretation

This result demonstrates that the generated HLS RTL can be placed and routed as an IP-level out-of-context block for the Zynq-7020 target while meeting the 10 ns timing constraint. The post-route WNS is positive, TNS is zero, and there are no timing failing endpoints.
