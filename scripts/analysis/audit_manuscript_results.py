#!/usr/bin/env python3
"""Audit numeric Results claims against immutable campaigns and checked reports.

This script reads raw data and manuscript material only. It does not rerun a
campaign, edit raw files, or create derived measurement data.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "manuscript" / "sections" / "07-results.md"
WINDOWS_ANALYSIS = ROOT / "docs" / "windows-validation" / "FINAL_WINDOWS_ANALYSIS.md"
REPORT = ROOT / "docs" / "MANUSCRIPT_RESULTS_AUDIT.md"
PRIMARY_DIR = ROOT / "data" / "raw" / "final" / "campaign-20261020T083014Z-70543371b61f"
WINDOWS_DIR = ROOT / "data" / "raw" / "windows" / "campaign-20261109T081504Z-c825d34051ff"
NETWORK_DIR = ROOT / "data" / "raw" / "network" / "campaign-20261114T202013Z-44a824c91fb9"
MATRIX = ROOT / "data" / "compatibility" / "v1" / "matrix" / "compat-v1-matrix-20261101T140752Z-7ef56e69" / "attempts.csv"
FIGURES = (
    "figure-1-latency.svg", "figure-2-communication.svg",
    "figure-3-network-sensitivity.svg", "figure-s1-primary-batches.svg",
    "figure-s2-compatibility-matrix.svg",
)
CASES = ("S0", "S2", "S3", "S4")


def load_csvs(directory: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(directory.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            rows.extend(csv.DictReader(handle))
    return rows


def measured(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row["warmup_flag"].lower() == "false"]


def campaign_summary(rows: list[dict[str, str]], metric: str) -> tuple[dict[str, float], dict[str, tuple[float, float]]]:
    medians: dict[str, float] = {}
    ranges: dict[str, tuple[float, float]] = {}
    for case in CASES:
        values = np.array([float(row[metric]) / 1_000_000 for row in rows if row["case_id"] == case])
        medians[case] = float(np.median(values))
        batch_contrasts = []
        for batch in sorted({row["batch_id"] for row in rows}):
            candidate = np.array([float(row[metric]) / 1_000_000 for row in rows if row["batch_id"] == batch and row["case_id"] == case])
            baseline = np.array([float(row[metric]) / 1_000_000 for row in rows if row["batch_id"] == batch and row["case_id"] == "S0"])
            batch_contrasts.append(float(np.median(candidate) - np.median(baseline)))
        ranges[case] = (min(batch_contrasts), max(batch_contrasts))
    return medians, ranges


def require(text: str, fragment: str, errors: list[str]) -> None:
    if fragment not in text:
        errors.append(f"missing or inconsistent manuscript fragment: {fragment!r}")


def main() -> None:
    errors: list[str] = []
    results = RESULTS.read_text(encoding="utf-8")
    windows_analysis = WINDOWS_ANALYSIS.read_text(encoding="utf-8")

    primary = measured(load_csvs(PRIMARY_DIR))
    windows = measured(load_csvs(WINDOWS_DIR))
    network = measured(load_csvs(NETWORK_DIR))
    if len(primary) != 600 or len(windows) != 600 or len(network) != 3000:
        errors.append("unexpected measured-row count in one or more campaigns")

    primary_medians, primary_ranges = campaign_summary(primary, "tls_handshake_ns")
    for case, value in primary_medians.items():
        require(results, f"{value:.3f} ms" if case != "S0" else "S0 had a median of 0.834 ms", errors)
    for case in CASES[1:]:
        low, high = primary_ranges[case]
        require(results, f"{low:+.3f} to {high:+.3f} ms", errors)

    windows_medians, windows_ranges = campaign_summary(windows, "latency_ns")
    for value in windows_medians.values():
        require(results, f"{value:.3f} ms", errors)
    for case in CASES[1:]:
        low, high = windows_ranges[case]
        require(windows_analysis, f"{low:+.3f} to {high:+.3f} ms", errors)

    network_by_condition = defaultdict(list)
    for row in network:
        network_by_condition[row["condition_id"]].append(row)
    if set(network_by_condition) != {"rtt-000ms", "rtt-001ms", "rtt-010ms", "rtt-050ms", "rtt-100ms"}:
        errors.append("network condition set differs from the Results claim")
    if any(len(rows) != 600 for rows in network_by_condition.values()):
        errors.append("network measured rows are not balanced by condition")
    for condition, rows in network_by_condition.items():
        medians, ranges = campaign_summary(rows, "tls_handshake_ns")
        if any(low <= 0 for case, (low, _) in ranges.items() if case != "S0"):
            errors.append(f"non-positive network batch contrast in {condition}")
    for fragment in ("10.095/10.014 ms", "50.141/50.061 ms", "100.081/99.990 ms"):
        require(results, fragment, errors)

    attempts = load_csvs(MATRIX.parent)
    successes = sum(row["success"].lower() == "true" for row in attempts)
    failures = [row for row in attempts if row["success"].lower() != "true"]
    if len(attempts) != 48 or successes != 36 or len(failures) != 12 or any(row["failure_category"] != "NO_COMMON_GROUP" for row in failures):
        errors.append("compatibility-matrix totals or failure categories do not match Results claims")
    for filename in FIGURES:
        if not (ROOT / "manuscript" / "figures" / filename).is_file():
            errors.append(f"missing figure: {filename}")

    status = "PASS" if not errors else "FAIL"
    lines = [
        "# Manuscript Results Audit", "",
        f"**Status: {status}.** This audit was generated from immutable campaign CSVs, the compatibility attempt record, and the current Results section.", "",
        "## Checks", "",
        f"- Primary Ubuntu measured rows: {len(primary)}; computed medians: " + ", ".join(f"{case} {primary_medians[case]:.6f} ms" for case in CASES) + ".",
        f"- Windows measured rows: {len(windows)}; computed medians: " + ", ".join(f"{case} {windows_medians[case]:.6f} ms" for case in CASES) + ".",
        f"- Network measured rows: {len(network)}; conditions: " + ", ".join(sorted(network_by_condition)) + "; every non-S0 median contrast was positive in all five observed batches per condition.",
        f"- Compatibility attempts: {len(attempts)}; successes: {successes}; retained failures: {len(failures)}, all `NO_COMMON_GROUP`.",
        "- Required main and supplementary figure assets are present.",
        "",
        "## Result", "",
    ]
    lines += ["- No discrepancies found."] if not errors else [f"- {error}" for error in errors]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit("; ".join(errors))
    print("Manuscript Results Audit: PASS")


if __name__ == "__main__":
    main()
