#!/usr/bin/env python3
"""Parse the Vitis HLS C-synthesis XML report.

This script mirrors the PySilicon-based workflow used in the course notebook:

    from pysilicon.utils.csynthparse import CsynthParser
    parser = CsynthParser(sol_path=...)
    parser.get_loop_pipeline_info()
    parser.get_resources()

It writes two grader-friendly CSV files:

    data/csynth_loop_info.csv
    data/csynth_resource_usage.csv

If PySilicon is not installed, the script falls back to a small local XML parser
so the report can still be inspected and regenerated.
"""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def find_solution_path(repo_root: Path, user_sol_path: str | None) -> Path | None:
    """Find a Vitis/Vivado HLS solution directory."""
    candidates = []
    if user_sol_path:
        candidates.append(Path(user_sol_path))
    candidates.extend([
        repo_root / "jpegls_hls_prj" / "solution1",
        repo_root / "jpegls_hls_cosim_prj" / "solution1",
        repo_root / "hls_component" / "solution1",
    ])

    for path in candidates:
        if path.exists():
            return path

    return None


def find_xml_report(repo_root: Path, sol_path: Path | None, user_xml: str | None) -> Path:
    """Find csynth.xml in common Vitis/Vivado HLS locations."""
    candidates = []
    if user_xml:
        candidates.append(Path(user_xml))

    if sol_path is not None:
        candidates.extend([
            sol_path / "syn" / "report" / "csynth.xml",
            sol_path / "syn" / "reports" / "csynth.xml",
            sol_path / "syn" / "report" / "jpegls_encode_hls_csynth.xml",
            sol_path / "syn" / "reports" / "jpegls_encode_hls_csynth.xml",
        ])

    candidates.extend([
        repo_root / "reports" / "csynth.xml",
        repo_root / "reports" / "jpegls_encode_hls_csynth.xml",
    ])

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError(
        "Could not find csynth.xml. Run `vitis_hls -f hls/run_hls.tcl` first, "
        "or pass --xml /path/to/csynth.xml."
    )


def parse_range_to_min_max(text: str) -> tuple[str, str]:
    """Convert HLS strings like '31 ~ 2483038208' into min/max fields."""
    text = (text or "").strip()
    if not text or text == "undef":
        return "", ""
    parts = [p.strip() for p in text.split("~")]
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], parts[-1]


def child_text(elem: ET.Element, tag: str, default: str = "") -> str:
    found = elem.find(tag)
    if found is None or found.text is None:
        return default
    return found.text.strip()


def fallback_parse_loop_info(xml_path: Path) -> list[dict[str, str]]:
    """Parse loop pipeline info from csynth.xml without PySilicon."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    rows: list[dict[str, str]] = []

    def add_loop(module_name: str, loop_elem: ET.Element) -> None:
        loop_name = child_text(loop_elem, "Name") or loop_elem.tag
        trip_min, trip_max = parse_range_to_min_max(child_text(loop_elem, "TripCount"))
        lat_min, lat_max = parse_range_to_min_max(child_text(loop_elem, "Latency"))

        rows.append({
            "Loop": f"{module_name}:{loop_name}" if module_name else loop_name,
            "PipelineII": child_text(loop_elem, "PipelineII"),
            "PipelineDepth": child_text(loop_elem, "PipelineDepth"),
            "TripCountMin": trip_min,
            "TripCountMax": trip_max,
            "LatencyMin": lat_min,
            "LatencyMax": lat_max,
        })

        metadata_tags = {
            "Name", "Slack", "TripCount", "Latency", "AbsoluteTimeLatency",
            "IterationLatency", "PipelineII", "PipelineDepth", "PipelineType",
            "InstanceList",
        }
        for child in list(loop_elem):
            if child.tag not in metadata_tags:
                if list(child):
                    add_loop(module_name, child)
                else:
                    rows.append({
                        "Loop": f"{module_name}:{child.tag}" if module_name else child.tag,
                        "PipelineII": "",
                        "PipelineDepth": "",
                        "TripCountMin": "",
                        "TripCountMax": "",
                        "LatencyMin": "",
                        "LatencyMax": "",
                    })

    modules = root.find("ModuleInformation")
    if modules is not None:
        for module in modules.findall("Module"):
            module_name = child_text(module, "Name")
            loop_summary = module.find("PerformanceEstimates/SummaryOfLoopLatency")
            if loop_summary is not None:
                for loop_elem in list(loop_summary):
                    add_loop(module_name, loop_elem)

    if not rows:
        loop_summary = root.find("PerformanceEstimates/SummaryOfLoopLatency")
        if loop_summary is not None:
            for loop_elem in list(loop_summary):
                add_loop("", loop_elem)

    return rows


def fallback_parse_resources(xml_path: Path) -> list[dict[str, str]]:
    """Parse resource usage from csynth.xml without PySilicon."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    resource_keys = ["BRAM_18K", "DSP", "FF", "LUT", "URAM"]
    rows: list[dict[str, str]] = []

    modules = root.find("ModuleInformation")
    if modules is not None:
        for module in modules.findall("Module"):
            resources = module.find("AreaEstimates/Resources")
            if resources is not None:
                row = {key: child_text(resources, key, "0") for key in resource_keys}
                row["Category"] = "module"
                row["Name"] = child_text(module, "Name", "unnamed_module")
                rows.append(row)

    top_resources = root.find("AreaEstimates/Resources")
    if top_resources is not None:
        row = {key: child_text(top_resources, key, "0") for key in resource_keys}
        row["Category"] = "top_total"
        row["Name"] = "jpegls_encode_hls"
        rows.append(row)

    available = root.find("AreaEstimates/AvailableResources")
    if available is not None:
        row = {key: child_text(available, key, "0") for key in resource_keys}
        row["Category"] = "available"
        row["Name"] = "xc7z020-clg484-1"
        rows.append(row)

    return rows


def write_loop_csv(rows: list[dict[str, str]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["", "PipelineII", "PipelineDepth", "TripCountMin", "TripCountMax", "LatencyMin", "LatencyMax"]
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "": row.get("Loop", ""),
                "PipelineII": row.get("PipelineII", ""),
                "PipelineDepth": row.get("PipelineDepth", ""),
                "TripCountMin": row.get("TripCountMin", ""),
                "TripCountMax": row.get("TripCountMax", ""),
                "LatencyMin": row.get("LatencyMin", ""),
                "LatencyMax": row.get("LatencyMax", ""),
            })


def write_resource_csv(rows: list[dict[str, str]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["Category", "Name", "BRAM_18K", "DSP", "FF", "LUT", "URAM"]
    with out_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "0" if key not in {"Category", "Name"} else "") for key in fieldnames})


def run_pysilicon_parser(sol_path: Path, data_dir: Path) -> bool:
    """Use the course PySilicon parser when available."""
    try:
        from pysilicon.utils.csynthparse import CsynthParser  # type: ignore
    except Exception as exc:
        print(f"INFO: PySilicon is not available ({exc}); using local XML fallback parser.")
        return False

    parser = CsynthParser(sol_path=str(sol_path))

    parser.get_loop_pipeline_info()
    parser.loop_df.to_csv(data_dir / "csynth_loop_info.csv", index=True)

    parser.get_resources()
    parser.res_df.to_csv(data_dir / "csynth_resource_usage.csv", index=False)

    print("Parsed with PySilicon CsynthParser.")
    print(f"Wrote {data_dir / 'csynth_loop_info.csv'}")
    print(f"Wrote {data_dir / 'csynth_resource_usage.csv'}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".", help="Repository root. Default: current directory.")
    ap.add_argument("--sol-path", default=None, help="Optional HLS solution path, e.g. jpegls_hls_prj/solution1.")
    ap.add_argument("--xml", default=None, help="Optional direct path to csynth.xml.")
    ap.add_argument("--out-dir", default="data", help="Output directory for CSV files. Default: data.")
    ap.add_argument("--fallback-only", action="store_true", help="Skip PySilicon and use the built-in XML parser.")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    data_dir = (repo_root / args.out_dir).resolve()
    sol_path = find_solution_path(repo_root, args.sol_path)

    if sol_path is not None:
        print(f"Using HLS solution path: {sol_path}")
    else:
        print("INFO: No generated HLS solution directory found; trying committed XML reports.")

    if not args.fallback_only and sol_path is not None and run_pysilicon_parser(sol_path, data_dir):
        return 0

    xml_path = find_xml_report(repo_root, sol_path, args.xml)
    print(f"Using XML report: {xml_path}")

    loop_rows = fallback_parse_loop_info(xml_path)
    resource_rows = fallback_parse_resources(xml_path)

    write_loop_csv(loop_rows, data_dir / "csynth_loop_info.csv")
    write_resource_csv(resource_rows, data_dir / "csynth_resource_usage.csv")

    print(f"Wrote {data_dir / 'csynth_loop_info.csv'} ({len(loop_rows)} rows)")
    print(f"Wrote {data_dir / 'csynth_resource_usage.csv'} ({len(resource_rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
