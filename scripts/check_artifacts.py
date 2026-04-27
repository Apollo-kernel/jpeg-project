#!/usr/bin/env python3
"""Lightweight consistency checker for the grader-ready repository.

This script uses only the Python standard library. It checks that the key
Markdown documents, source files, CSV evidence, and report files are present,
and verifies that all committed result CSV rows are marked PASS.
"""

from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    ".gitignore",
    "Makefile",
    "submitted_results.json",
    "docs/grader_checklist.md",
    "docs/ip_role_definition.md",
    "docs/architecture.md",
    "docs/verification_evaluation.md",
    "docs/scope_and_limitations.md",
    "docs/reproducibility.md",
    "docs/cosim_status.md",
    "docs/llm_grader_submission_notes.md",
    "hls/jpegls_hls.cpp",
    "hls/jpegls_hls.hpp",
    "hls/jpegls_hls_tb.cpp",
    "hls/run_hls.tcl",
    "hls/run_hls_cosim_small.tcl",
    "scripts/vivado_impl_reports.tcl",
    "scripts/parse_csynth_pysilicon.py",
    "reports/jpegls_encode_hls_csynth.rpt",
    "reports/csynth.xml",
    "reports/jpegls_cosim_report.md",
    "reports/cosim_pass_excerpt.txt",
    "reports/vivado_implementation_summary.md",
    "reports/vivado_ooc_pass_excerpt.txt",
    "reports/vivado_timing.rpt",
    "reports/vivado_utilization.rpt",
    "reports/vivado_power.rpt",
    "data/python_results.csv",
    "data/hls_csim_results.csv",
    "data/hls_cosim_small_results.csv",
    "data/csynth_loop_info.csv",
    "data/csynth_resource_usage.csv",
    "data/artifact_manifest.csv",
]

CSV_CHECKS = {
    "data/python_results.csv": "result",
    "data/hls_csim_results.csv": "result",
    "data/hls_cosim_small_results.csv": "result",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    raise SystemExit(1)


def main() -> int:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    if missing:
        fail("missing required files:\n  " + "\n  ".join(missing))

    for rel, col in CSV_CHECKS.items():
        path = ROOT / rel
        with path.open(newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            fail(f"{rel} has no data rows")
        bad = [r for r in rows if r.get(col) != "PASS"]
        if bad:
            fail(f"{rel} has non-PASS rows: {bad[:3]}")
        print(f"PASS: {rel} has {len(rows)} PASS rows")

    forbidden_dirs = [".Xil", "jpegls_hls_prj", "jpegls_hls_cosim_prj", "vivado_ooc_impl_prj", "__MACOSX"]
    present = [d for d in forbidden_dirs if (ROOT / d).exists()]
    if present:
        fail("generated/bloated directories are present: " + ", ".join(present))

    print("PASS: required grader artifacts are present and result CSVs are consistent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
