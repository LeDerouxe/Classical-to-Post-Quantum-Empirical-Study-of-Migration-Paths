#!/usr/bin/env python3
"""Audit the deterministic JISA packaging without fabricating author facts."""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "submission" / "jisa" / "jisa-submission-manuscript-en.md"
DOCX = ROOT / "submission" / "jisa" / "jisa-submission-manuscript-en.docx"
FIGURES = ROOT / "submission" / "jisa" / "figures-png"


def main() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    errors: list[str] = []
    advisories: list[str] = []
    for required in (
        "Amirreza Rezaee",
        "Peyman Neamatollahi",
        "LeDerouxe@gmail.com",
        "Hakim Sabzevari University",
        "## CRediT authorship contribution statement",
        "## Funding",
        "## Declaration of competing interest",
        "## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process",
        "Data and Code Availability",
        "## References",
    ):
        if required not in text:
            errors.append(f"missing required submission element: {required}")
    if "[@" in text:
        errors.append("unconverted authoring citation key found")
    for number in range(1, 8):
        if not re.search(rf"\[{number}\]", text):
            errors.append(f"citation/reference number [{number}] absent")
    refs = re.findall(r"(?m)^\[(\d+)\] ", text.split("## References", 1)[-1])
    if refs != [str(n) for n in range(1, 8)]:
        errors.append(f"unexpected reference list numbering: {refs}")
    if not DOCX.exists() or DOCX.stat().st_size < 100_000:
        errors.append("Word manuscript is missing or unexpectedly small")
    for name in ("figure-1-latency", "figure-2-communication", "figure-3-network-sensitivity", "figure-s1-primary-batches", "figure-s2-compatibility-matrix"):
        if not (FIGURES / f"{name}.png").exists():
            errors.append(f"missing rasterized figure: {name}")
    if "Author confirmation required" in text:
        advisories.append("author declarations are deliberately unresolved; do not submit until both authors confirm and replace them")

    print("JISA submission package audit: " + ("PASS" if not errors else "FAIL"))
    for item in errors:
        print("ERROR: " + item)
    for item in advisories:
        print("ADVISORY: " + item)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
