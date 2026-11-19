#!/usr/bin/env python3
"""Check the bibliographic completeness of sources cited in the main drafts."""
from __future__ import annotations

import re
from pathlib import Path

from audit_main_draft_citations import APPROVED, ARTICLES, BIBLIOGRAPHY


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "BIBLIOGRAPHY_AUDIT.md"


def citation_keys(text: str) -> set[str]:
    return set(re.findall(r"\[@([A-Za-z0-9]+)\]", text))


def entries(text: str) -> dict[str, str]:
    blocks = re.split(r"(?=^@\w+\{)", text, flags=re.MULTILINE)
    result: dict[str, str] = {}
    for block in blocks:
        match = re.match(r"@(\w+)\{([^,]+),", block)
        if match:
            result[match.group(2)] = block
    return result


def field(block: str, name: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(name)}\s*=\s*\{{([^}}]+)\}}", block, re.MULTILINE)
    return match.group(1).strip() if match else None


def main() -> None:
    cited = set().union(*(citation_keys(path.read_text(encoding="utf-8")) for path in ARTICLES.values()))
    bib_entries = entries(BIBLIOGRAPHY.read_text(encoding="utf-8"))
    errors: list[str] = []
    rows: list[tuple[str, str, str, str]] = []
    for key in sorted(cited):
        block = bib_entries.get(key)
        if block is None:
            errors.append(f"cited key missing from bibliography: {key}")
            continue
        missing = [name for name in ("author", "title", "year", "doi") if not field(block, name)]
        doi = field(block, "doi") or ""
        if missing:
            errors.append(f"{key} missing required field(s): {', '.join(missing)}")
        if not re.fullmatch(r"10\.\d{4,9}/\S+", doi):
            errors.append(f"{key} has malformed DOI: {doi!r}")
        if key not in APPROVED:
            errors.append(f"{key} is cited but has no claim-level evidence-matrix approval")
        result = "Pass" if not missing and re.fullmatch(r"10\.\d{4,9}/\S+", doi) and key in APPROVED else "Fail"
        rows.append((key, field(block, "year") or "missing", doi or "missing", result))

    uncited = sorted(set(bib_entries) - cited)
    if uncited:
        errors.append("bibliography contains uncited entry or entries: " + ", ".join(uncited))

    status = "PASS" if not errors else "FAIL"
    lines = [
        "# Bibliography Audit", "",
        f"**Status: {status}.** This audit checks every source cited in both main drafts for required BibTeX fields, DOI syntax, and claim-level approval.", "",
        "## Cited entries", "",
        "| BibTeX key | Year | DOI | Result |", "| --- | ---: | --- | --- |",
    ]
    lines.extend(f"| `{key}` | {year} | `{doi}` | {result} |" for key, year, doi, result in rows)
    lines += ["", "## Result", ""]
    lines += ["- All cited bibliography entries are complete, DOI-bearing, and evidence-matrix approved."] if not errors else [f"- {error}" for error in errors]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit("; ".join(errors))
    print("Bibliography Audit: PASS")


if __name__ == "__main__":
    main()
