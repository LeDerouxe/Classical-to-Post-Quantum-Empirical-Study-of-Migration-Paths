#!/usr/bin/env python3
"""Render the controlled network-sensitivity manuscript figure from derived data."""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = "campaign-20261114T202013Z-44a824c91fb9"
SUMMARY = ROOT / "data" / "processed" / "network" / CAMPAIGN / "latency-summary.csv"
OUTPUT = ROOT / "manuscript" / "figures" / "figure-3-network-sensitivity.svg"
CASES = ("S0", "S2", "S3", "S4")
CONDITIONS = ("rtt-000ms", "rtt-001ms", "rtt-010ms", "rtt-050ms", "rtt-100ms")
LABELS = ("0", "1", "10", "50", "100")
COLORS = {"S0": "#1f2937", "S2": "#0072B2", "S3": "#D55E00", "S4": "#009E73"}


def main() -> None:
    with SUMMARY.open(newline="", encoding="utf-8") as handle:
        records = list(csv.DictReader(handle))
    lookup = {(item["condition"], item["case"]): item for item in records}
    if set(lookup) != {(condition, case) for condition in CONDITIONS for case in CASES}:
        raise SystemExit("Unexpected condition/case combinations in derived summary")
    width, height = 980, 495
    left, right, top, bottom = 100, 40, 85, 80
    plot_width, plot_height = width - left - right, height - top - bottom
    maximum = 220.0
    x = lambda index: left + index * plot_width / (len(CONDITIONS) - 1)
    y = lambda value: top + plot_height - value / maximum * plot_height
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">TLS handshake duration across controlled added RTT conditions</title>',
        '<desc id="desc">Condition-specific medians and batch-aware 95 percent bootstrap confidence intervals for four TLS configurations across zero, one, ten, fifty, and one hundred milliseconds of added RTT.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111827}.small{font-size:13px}.label{font-size:16px}.title{font-size:20px;font-weight:600}.axis{stroke:#6b7280;stroke-width:1}.grid{stroke:#d1d5db;stroke-width:1}.ci{stroke-width:2}.line{fill:none;stroke-width:2.5}</style>',
        '<text x="100" y="31" class="title">Controlled network-sensitivity follow-up</text>',
        '<text x="100" y="53" class="small">Median and batch-aware 95% bootstrap interval; n = 150 per configuration and RTT condition</text>',
    ]
    for tick in range(0, 221, 25):
        yy = y(tick)
        lines += [f'<line x1="{left}" y1="{yy:.1f}" x2="{width-right}" y2="{yy:.1f}" class="grid"/>', f'<text x="{left-12}" y="{yy+5:.1f}" text-anchor="end" class="small">{tick}</text>']
    for index, label in enumerate(LABELS):
        xx = x(index)
        lines += [f'<line x1="{xx:.1f}" y1="{top}" x2="{xx:.1f}" y2="{height-bottom}" class="grid"/>', f'<text x="{xx:.1f}" y="{height-bottom+25}" text-anchor="middle" class="small">{label}</text>']
    lines += [f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>', f'<text x="{left-63}" y="{top + plot_height/2:.1f}" transform="rotate(-90 {left-63} {top + plot_height/2:.1f})" text-anchor="middle" class="label">Client SSL_connect duration (ms)</text>', f'<text x="{left+plot_width/2:.1f}" y="{height-20}" text-anchor="middle" class="label">Added RTT (ms)</text>']
    for case in CASES:
        points = []
        for index, condition in enumerate(CONDITIONS):
            item = lookup[condition, case]
            median, low, high = (float(item[field]) for field in ("median_ms", "median_ci_low_ms", "median_ci_high_ms"))
            xx = x(index)
            points.append(f'{xx:.1f},{y(median):.1f}')
            lines += [f'<line x1="{xx:.1f}" y1="{y(low):.1f}" x2="{xx:.1f}" y2="{y(high):.1f}" stroke="{COLORS[case]}" class="ci"/>', f'<line x1="{xx-5:.1f}" y1="{y(low):.1f}" x2="{xx+5:.1f}" y2="{y(low):.1f}" stroke="{COLORS[case]}" class="ci"/>', f'<line x1="{xx-5:.1f}" y1="{y(high):.1f}" x2="{xx+5:.1f}" y2="{y(high):.1f}" stroke="{COLORS[case]}" class="ci"/>']
        lines.append(f'<polyline points="{" ".join(points)}" stroke="{COLORS[case]}" class="line"/>')
        for index, condition in enumerate(CONDITIONS):
            median = float(lookup[condition, case]["median_ms"])
            lines.append(f'<circle cx="{x(index):.1f}" cy="{y(median):.1f}" r="4.5" fill="{COLORS[case]}"/>')
    for index, case in enumerate(CASES):
        xx = 560 + index * 90
        lines += [f'<line x1="{xx}" y1="70" x2="{xx+20}" y2="70" stroke="{COLORS[case]}" class="line"/>', f'<circle cx="{xx+10}" cy="70" r="4" fill="{COLORS[case]}"/>', f'<text x="{xx+27}" y="75" class="small">{case}</text>']
    lines.append('</svg>')
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
