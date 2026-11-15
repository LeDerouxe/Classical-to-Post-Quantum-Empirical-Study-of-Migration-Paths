#!/usr/bin/env python3
"""Render supplementary manuscript SVG figures from checked study outputs."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRIMARY = ROOT / "data" / "processed" / "final" / "campaign-20261020T083014Z-70543371b61f" / "batch-latency-summary.csv"
MATRIX = ROOT / "data" / "compatibility" / "v1" / "matrix" / "compat-v1-matrix-20261101T140752Z-7ef56e69" / "attempts.csv"
OUTPUT = ROOT / "manuscript" / "figures"
CASES = ("S0", "S2", "S3", "S4")
PROFILES = ("L", "H", "D", "Q")
COLORS = {"S0": "#1f2937", "S2": "#0072B2", "S3": "#D55E00", "S4": "#009E73"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def primary_batch_view() -> None:
    data = rows(PRIMARY)
    by_case = {case: [item for item in data if item["case"] == case] for case in CASES}
    if any(len(items) != 5 for items in by_case.values()):
        raise SystemExit("Expected five primary-batch medians per case")
    width, height, left, right, top, bottom = 920, 435, 115, 60, 80, 75
    plot_width, plot_height = width - left - right, height - top - bottom
    maximum = 1.7
    x = lambda index: left + index * plot_width / (len(CASES) - 1)
    y = lambda value: top + plot_height - value / maximum * plot_height
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Primary Ubuntu batch-level TLS handshake medians</title>',
        '<desc id="desc">Five retained batch medians per TLS configuration in the primary Ubuntu loopback study.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111827}.small{font-size:13px}.label{font-size:16px}.title{font-size:20px;font-weight:600}.axis{stroke:#6b7280;stroke-width:1}.grid{stroke:#d1d5db;stroke-width:1}.median{stroke-width:3}</style>',
        '<text x="115" y="32" class="title">Primary Ubuntu batch-level handshake medians</text>',
        '<text x="115" y="53" class="small">Five completed batches per configuration; points are not individual handshakes</text>',
    ]
    for tick in range(0, 18, 2):
        value = tick / 10
        yy = y(value)
        lines += [f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" class="grid"/>', f'<text x="{left-12}" y="{yy+5:.1f}" text-anchor="end" class="small">{value:.1f}</text>']
    for index, case in enumerate(CASES):
        xx = x(index)
        lines += [f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{height-bottom}" class="grid"/>', f'<text x="{xx:.1f}" y="{height-bottom+27}" text-anchor="middle" class="label">{case}</text>']
        values = sorted(float(item["median_ms"]) for item in by_case[case])
        offsets = (-18, -9, 0, 9, 18)
        for value, offset in zip(values, offsets):
            lines.append(f'<circle cx="{xx+offset:.1f}" cy="{y(value):.1f}" r="4.5" fill="{COLORS[case]}"/>')
        median = sorted(values)[2]
        lines.append(f'<line x1="{xx-27:.1f}" y1="{y(median):.1f}" x2="{xx+27:.1f}" y2="{y(median):.1f}" stroke="{COLORS[case]}" class="median"/>')
    lines += [f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>', f'<text x="48" y="{top+plot_height/2:.1f}" transform="rotate(-90 48 {top+plot_height/2:.1f})" text-anchor="middle" class="label">Batch median SSL_connect duration (ms)</text>', '<text x="115" y="408" class="small">Short horizontal bar: median of the five batch medians. Full observation-level inference is reported in Figure 1.</text>', '</svg>']
    write(OUTPUT / "figure-s1-primary-batches.svg", lines)


def compatibility_matrix() -> None:
    data = rows(MATRIX)
    counts: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
    for item in data:
        key = item["client_profile"], item["server_profile"]
        counts[key][1] += 1
        counts[key][0] += item["success"].lower() == "true"
    if set(counts) != {(client, server) for client in PROFILES for server in PROFILES} or any(total != 3 for _, total in counts.values()):
        raise SystemExit("Expected all 16 profile pairs with three attempts each")
    width, height, left, top, cell = 700, 580, 180, 135, 105
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Native OpenSSL migration-profile compatibility matrix</title>',
        '<desc id="desc">Successes out of three fresh attempts for every ordered client and server profile pair. Failures were recorded as no common group.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111827}.small{font-size:13px}.label{font-size:16px}.title{font-size:20px;font-weight:600}.cell{stroke:#d1d5db;stroke-width:1}</style>',
        '<text x="55" y="35" class="title">Migration-profile compatibility</text>',
        '<text x="55" y="57" class="small">Native OpenSSL 3.5.9; fresh attempts; each cell reports success / 3</text>',
        '<text x="390" y="100" text-anchor="middle" class="label">Server profile</text>',
        '<text x="45" y="345" transform="rotate(-90 45 345)" text-anchor="middle" class="label">Client profile</text>',
    ]
    for index, profile in enumerate(PROFILES):
        coord = left + index * cell + cell / 2
        lines += [f'<text x="{coord:.1f}" y="{top-16}" text-anchor="middle" class="label">{profile}</text>', f'<text x="{left-16}" y="{top+index*cell+cell/2+6:.1f}" text-anchor="end" class="label">{profile}</text>']
    for row, client in enumerate(PROFILES):
        for col, server in enumerate(PROFILES):
            success, total = counts[client, server]
            x, y = left + col * cell, top + row * cell
            fill = "#d1fae5" if success == total else "#fee2e2"
            lines += [f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}" class="cell"/>', f'<text x="{x+cell/2}" y="{y+48}" text-anchor="middle" class="label">{success}/{total}</text>', f'<text x="{x+cell/2}" y="{y+74}" text-anchor="middle" class="small">{"TLS success" if success == total else "no common group"}</text>']
    lines += ['<rect x="180" y="560" width="14" height="14" fill="#d1fae5"/><text x="201" y="572" class="small">all three attempts succeeded</text>', '<rect x="421" y="560" width="14" height="14" fill="#fee2e2"/><text x="442" y="572" class="small">all three failures: no common group</text>', '</svg>']
    write(OUTPUT / "figure-s2-compatibility-matrix.svg", lines)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    primary_batch_view()
    compatibility_matrix()
    print("Rendered supplementary figures.")


if __name__ == "__main__":
    main()
