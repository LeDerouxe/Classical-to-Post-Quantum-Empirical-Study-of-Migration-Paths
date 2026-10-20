#!/usr/bin/env python3
"""Render manuscript SVG figures from the derived final Ubuntu summaries.

Run analyze_final_campaign.py first. This renderer does not read or modify raw
observations; it turns the checked derived summaries into versioned figures.
"""
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = "campaign-20261020T083014Z-70543371b61f"
DERIVED = ROOT / "data" / "processed" / "final" / CAMPAIGN
OUTPUT = ROOT / "manuscript" / "figures"
COLORS = {"S0": "#1f2937", "S2": "#0072B2", "S3": "#D55E00", "S4": "#009E73"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def figure_latency(data: list[dict[str, str]]) -> None:
    width, height = 920, 390
    left, right, top, bottom = 145, 55, 70, 65
    plot_width = width - left - right
    domain_max = 1.6
    x = lambda value: left + float(value) / domain_max * plot_width
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">TLS handshake latency by cryptographic configuration</title>',
        '<desc id="desc">Medians and batch-aware 95 percent bootstrap confidence intervals for S0, S2, S3, and S4.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111827}.small{font-size:13px}.label{font-size:16px}.title{font-size:20px;font-weight:600}.axis{stroke:#6b7280;stroke-width:1}.grid{stroke:#d1d5db;stroke-width:1}</style>',
        '<text x="145" y="32" class="title">TLS 1.3 handshake latency</text>',
        '<text x="145" y="53" class="small">Median and batch-aware 95% bootstrap confidence interval; n = 150 per configuration</text>',
    ]
    for tick in range(0, 9):
        value = tick * 0.2
        tx = x(value)
        lines.extend([
            f'<line x1="{tx:.1f}" y1="{top}" x2="{tx:.1f}" y2="{height-bottom}" class="grid"/>',
            f'<text x="{tx:.1f}" y="{height-bottom+24}" text-anchor="middle" class="small">{value:.1f}</text>',
        ])
    lines.extend([
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" class="axis"/>',
        f'<text x="{left + plot_width/2:.1f}" y="{height-14}" text-anchor="middle" class="label">Client SSL_connect duration (ms)</text>',
    ])
    for index, item in enumerate(data):
        case = item["case"]
        y = top + 48 + index * 57
        median = float(item["median_ms"])
        low = float(item["median_ci_low_ms"])
        high = float(item["median_ci_high_ms"])
        color = COLORS[case]
        lines.extend([
            f'<text x="{left-18}" y="{y+5}" text-anchor="end" class="label">{case}</text>',
            f'<line x1="{x(low):.1f}" y1="{y}" x2="{x(high):.1f}" y2="{y}" stroke="{color}" stroke-width="3"/>',
            f'<line x1="{x(low):.1f}" y1="{y-8}" x2="{x(low):.1f}" y2="{y+8}" stroke="{color}" stroke-width="2"/>',
            f'<line x1="{x(high):.1f}" y1="{y-8}" x2="{x(high):.1f}" y2="{y+8}" stroke="{color}" stroke-width="2"/>',
            f'<circle cx="{x(median):.1f}" cy="{y}" r="6" fill="{color}"/>',
            f'<text x="{x(high)+12:.1f}" y="{y+5}" class="small">{median:.3f} ms</text>',
        ])
    lines.append('</svg>')
    write(OUTPUT / "figure-1-latency.svg", lines)


def figure_communication(data: list[dict[str, str]]) -> None:
    width, height = 920, 470
    top, bottom = 90, 55
    panels = [(95, 360, "handshake_bytes_median", "Handshake bytes", 12000),
              (545, 300, "packet_count_median", "TCP segments", 14)]
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">TLS handshake communication overhead by configuration</title>',
        '<desc id="desc">Client-side TCP_INFO median handshake bytes and packet counts for S0, S2, S3, and S4.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#111827}.small{font-size:13px}.label{font-size:16px}.title{font-size:20px;font-weight:600}.axis{stroke:#6b7280;stroke-width:1}.grid{stroke:#d1d5db;stroke-width:1}</style>',
        '<text x="95" y="32" class="title">TLS 1.3 communication overhead</text>',
        '<text x="95" y="53" class="small">Client-side TCP_INFO at SSL_connect completion; n = 150 per configuration</text>',
    ]
    for left, panel_width, metric, title, maximum in panels:
        plot_left = left + 58
        plot_width = panel_width - 58
        x = lambda value: plot_left + float(value) / maximum * plot_width
        lines.append(f'<text x="{left}" y="{top}" class="label">{title}</text>')
        for tick in range(5):
            value = maximum * tick / 4
            tx = x(value)
            label = f'{int(value):,}'
            lines.extend([
                f'<line x1="{tx:.1f}" y1="{top+22}" x2="{tx:.1f}" y2="{height-bottom}" class="grid"/>',
                f'<text x="{tx:.1f}" y="{height-bottom+22}" text-anchor="middle" class="small">{label}</text>',
            ])
        for index, item in enumerate(data):
            case = item["case"]
            y = top + 45 + index * 63
            value = float(item[metric])
            color = COLORS[case]
            lines.extend([
                f'<text x="{plot_left-11}" y="{y+15}" text-anchor="end" class="small">{case}</text>',
                f'<rect x="{plot_left}" y="{y}" width="{max(1, x(value)-plot_left):.1f}" height="25" fill="{color}"/>',
                f'<text x="{min(x(value)+8, left+panel_width-4):.1f}" y="{y+17}" class="small">{int(value):,}</text>',
            ])
    lines.append('</svg>')
    write(OUTPUT / "figure-2-communication.svg", lines)


def main() -> None:
    latency = rows(DERIVED / "latency-summary.csv")
    communication = rows(DERIVED / "communication-summary.csv")
    if [row["case"] for row in latency] != ["S0", "S2", "S3", "S4"]:
        raise SystemExit("Unexpected latency-summary case order")
    if [row["case"] for row in communication] != ["S0", "S2", "S3", "S4"]:
        raise SystemExit("Unexpected communication-summary case order")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    figure_latency(latency)
    figure_communication(communication)
    print("Rendered manuscript figures from checked derived summaries.")


if __name__ == "__main__":
    main()
