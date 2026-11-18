#!/usr/bin/env python3
"""Verify that citations in both main drafts are present and pre-approved.

The check is deliberately narrow: it validates citation keys, their presence in
the bibliography, and their mapping to the claim-level evidence matrix. It does
not replace human review of whether an individual sentence stays within the
approved claim wording.
"""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTICLES = {
    "English": ROOT / "manuscript" / "article-en.md",
    "Persian": ROOT / "manuscript" / "article-fa.md",
}
BIBLIOGRAPHY = ROOT / "manuscript" / "references.bib"
EVIDENCE_MATRIX = ROOT / "docs" / "citations" / "EVIDENCE_MATRIX.md"
REPORT = ROOT / "docs" / "MAIN_DRAFT_CITATION_AUDIT.md"

# BibTeX key -> evidence-matrix identifier. The mapping is intentionally
# explicit so introducing a new source requires human claim-level approval.
APPROVED = {
    "TLS9846": "TLS-9846",
    "NISTFIPS203": "NIST-203",
    "NISTFIPS204": "NIST-204",
    "RFC10024": "RFC-10024",
    "Sikeridis2020": "SIKERIDIS-2020",
    "Sosnowski2023": "SOSNOWSKI-2023",
    "Montenegro2026": "MONTENEGRO-2026",
}


def citation_keys(text: str) -> set[str]:
    return set(re.findall(r"\[@([A-Za-z0-9]+)\]", text))


def bibliography_keys(text: str) -> set[str]:
    return set(re.findall(r"@\w+\{([^,]+),", text))


def main() -> None:
    article_keys = {
        language: citation_keys(path.read_text(encoding="utf-8"))
        for language, path in ARTICLES.items()
    }
    bib_keys = bibliography_keys(BIBLIOGRAPHY.read_text(encoding="utf-8"))
    evidence = EVIDENCE_MATRIX.read_text(encoding="utf-8")
    errors: list[str] = []

    if article_keys["English"] != article_keys["Persian"]:
        errors.append("English and Persian main drafts cite different key sets")
    for language, keys in article_keys.items():
        for key in sorted(keys):
            if key not in bib_keys:
                errors.append(f"{language} main draft cites missing BibTeX key: {key}")
            matrix_id = APPROVED.get(key)
            if matrix_id is None:
                errors.append(f"{language} main draft cites a key without evidence-matrix approval: {key}")
            elif matrix_id not in evidence:
                errors.append(f"evidence-matrix identifier is missing: {matrix_id}")

    status = "PASS" if not errors else "FAIL"
    keys = sorted(article_keys["English"] | article_keys["Persian"])
    lines = [
        "# Main-Draft Citation Audit", "",
        f"**Status: {status}.** This audit checks citation keys in the English and Persian main drafts against the committed bibliography and the claim-level evidence matrix.", "",
        "## Approved citations in use", "",
        "| BibTeX key | Evidence-matrix identifier |", "| --- | --- |",
    ]
    lines.extend(f"| `{key}` | `{APPROVED.get(key, 'unapproved')}` |" for key in keys)
    lines += ["", "## Result", ""]
    lines += ["- No missing, mismatched, or unapproved citation keys found."] if not errors else [f"- {error}" for error in errors]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit("; ".join(errors))
    print("Main-Draft Citation Audit: PASS")


if __name__ == "__main__":
    main()
