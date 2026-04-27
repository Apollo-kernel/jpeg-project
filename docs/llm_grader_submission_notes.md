# LLM Grader Submission Notes

Use this file as the brief note in the assignment submission, after the GitHub URL.

```text
Please start with README.md, then inspect docs/grader_checklist.md and docs/cosim_status.md.

This project implements a JPEG-LS regular-mode inspired 8-bit grayscale lossless encoder datapath. The IP interface is documented in docs/ip_role_definition.md. The architecture and module partitioning are documented in docs/architecture.md. Verification evidence includes Python golden-model results, HLS C simulation for 8/8 tests, Vitis HLS synthesis reports and XML parsing, real C/RTL co-simulation PASS evidence for 6/6 small synthetic tests, and Vivado out-of-context post-route timing/utilization/power reports. The clean repository excludes generated Vitis/Vivado project directories and root log/journal files; curated report summaries and PASS excerpts are committed under reports/.
```

## Important Honesty Note

The C/RTL co-simulation PASS is real, but it was intentionally run only on the six 8x8 synthetic vectors. The two 512x768 real images are verified by Python and HLS C simulation, not by full-size C/RTL co-simulation. This distinction is documented in `docs/cosim_status.md` and `reports/jpegls_cosim_report.md`.
