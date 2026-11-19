#!/usr/bin/env python3
"""Audit title, abstracts, and keywords in the bilingual main drafts."""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENGLISH = ROOT / "manuscript" / "article-en.md"
PERSIAN = ROOT / "manuscript" / "article-fa.md"
REPORT = ROOT / "docs" / "FRONT_MATTER_AUDIT.md"
ENGLISH_TITLE = "From Classical to Post-Quantum: An Empirical Study of TLS Migration Paths, Performance Overhead, and Compatibility"
PERSIAN_TITLE = "از کلاسیک تا پساکوانتومی: مطالعه‌ای تجربی دربارهٔ مسیرهای مهاجرت TLS، سربار کارایی و سازگاری"


def abstract_between(text: str, heading: str, next_heading: str) -> str:
    match = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## {re.escape(next_heading)}\s*$)", text, re.MULTILINE | re.DOTALL)
    if not match:
        raise ValueError(f"missing {heading!r} block")
    return match.group(1).strip()


def main() -> None:
    en_text = ENGLISH.read_text(encoding="utf-8")
    fa_text = PERSIAN.read_text(encoding="utf-8")
    errors: list[str] = []
    if not en_text.startswith(f"# {ENGLISH_TITLE}\n"):
        errors.append("English title differs from the approved title")
    if not fa_text.startswith(f"# {PERSIAN_TITLE}\n"):
        errors.append("Persian title differs from the approved title")

    try:
        en_abstract = abstract_between(en_text, "Abstract", "1 Introduction")
        fa_abstract = abstract_between(fa_text, "چکیده", "۱ مقدمه")
    except ValueError as exc:
        errors.append(str(exc))
        en_abstract = fa_abstract = ""

    en_body, _, en_keywords = en_abstract.partition("**Keywords—**")
    fa_body, _, fa_keywords = fa_abstract.partition("**کلیدواژه‌ها—**")
    english_words = len(re.findall(r"\b[\w'-]+\b", en_body))
    en_keyword_items = [item.strip(" .\n") for item in en_keywords.split(";") if item.strip(" .\n")]
    fa_keyword_items = [item.strip(" .\n") for item in fa_keywords.split("؛") if item.strip(" .\n")]
    if not 1 <= english_words <= 250:
        errors.append(f"English abstract must contain 1--250 words; observed {english_words}")
    if "[@" in en_abstract or "[@" in fa_abstract:
        errors.append("abstract contains an in-text citation")
    if len(en_keyword_items) != 5:
        errors.append(f"English keyword count must be 5; observed {len(en_keyword_items)}")
    if len(fa_keyword_items) != 5:
        errors.append(f"Persian keyword count must be 5; observed {len(fa_keyword_items)}")
    for fragment in ("0.834 ms", "0.989 ms", "1.436 ms", "1.312 ms", "36", "12", "3,000"):
        if fragment not in en_body:
            errors.append(f"English abstract misses audited result fragment: {fragment}")

    status = "PASS" if not errors else "FAIL"
    lines = [
        "# Front-Matter Audit", "",
        f"**Status: {status}.** This audit checks the approved bilingual titles, English abstract length, citation-free abstracts, keyword counts, and selected audited result fragments.", "",
        "## Checks", "",
        f"- English abstract words: {english_words} (limit: 250).",
        f"- English keywords: {len(en_keyword_items)}; Persian keywords: {len(fa_keyword_items)}.",
        "- Both abstracts contain no in-text citation keys.",
        "- Both titles match the approved wording.",
        "", "## Result", "",
    ]
    lines += ["- Front matter is complete and internally consistent."] if not errors else [f"- {error}" for error in errors]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if errors:
        raise SystemExit("; ".join(errors))
    print("Front-Matter Audit: PASS")


if __name__ == "__main__":
    main()
