#!/usr/bin/env python3
"""Build a JISA initial-submission package from the audited English draft.

This script deliberately performs only deterministic editorial packaging: it
adds author metadata supplied by the author team, converts frozen citation keys
to JISA-style numerical citations, appends the frozen bibliography, and adds
submission declarations that still require author confirmation where a fact
cannot be inferred from the repository.
"""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "article-en.md"
OUT = ROOT / "submission" / "jisa"

TITLE = "From Classical to Post-Quantum: An Empirical Study of TLS Migration Paths, Performance Overhead, and Compatibility"
AFFILIATION = "Department of Computer Engineering, Faculty of Electrical and Computer Engineering, Hakim Sabzevari University, Sabzevar, Iran"

REFERENCES = """[1] E. Rescorla, The Transport Layer Security (TLS) Protocol Version 1.3, RFC 9846, Internet Engineering Task Force, July 2026. https://doi.org/10.17487/RFC9846.

[2] National Institute of Standards and Technology, Module-Lattice-Based Key-Encapsulation Mechanism Standard, FIPS 203, August 2024. https://doi.org/10.6028/NIST.FIPS.203.

[3] National Institute of Standards and Technology, Module-Lattice-Based Digital Signature Standard, FIPS 204, August 2024. https://doi.org/10.6028/NIST.FIPS.204.

[4] K. Kwiatkowski, P. Kampanakis, B. E. Westerbaan, and D. Stebila, Post-Quantum Traditional (PQ/T) Hybrid Key Agreement Mechanisms for TLS 1.3, RFC 10024, Internet Engineering Task Force, August 2026. https://doi.org/10.17487/RFC10024.

[5] D. Sikeridis, P. Kampanakis, and M. Devetsikiotis, Post-Quantum Authentication in TLS 1.3: A Performance Study, in: Network and Distributed System Security Symposium, 2020. https://doi.org/10.14722/ndss.2020.24203.

[6] M. Sosnowski, F. Wiedner, E. Hauser, L. Steger, D. Schoinianakis, S. Gallenm\u00fcller, and G. Carle, The Performance of Post-Quantum TLS 1.3, in: Companion of the 19th International Conference on Emerging Networking EXperiments and Technologies, 2023, pp. 19-27. https://doi.org/10.1145/3624354.3630585.

[7] J. A. Montenegro, R. Rios, and J. L\u00f3pez-Cerezo, A Performance Evaluation Framework for Post-Quantum TLS, Future Generation Computer Systems 175 (2026) 108062. https://doi.org/10.1016/j.future.2025.108062.
"""

CITATIONS = {
    "[@TLS9846]": "[1]",
    "[@NISTFIPS203]": "[2]",
    "[@NISTFIPS204]": "[3]",
    "[@RFC10024]": "[4]",
    "[@Sikeridis2020]": "[5]",
    "[@Sosnowski2023]": "[6]",
    "[@Montenegro2026]": "[7]",
}


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    body, _references = text.split("\n## References\n", 1)
    for authoring_key, numeric in CITATIONS.items():
        body = body.replace(authoring_key, numeric)
    if "[@" in body:
        raise SystemExit("unconverted authoring citation key found")

    old_title = f"# {TITLE}\n"
    if not body.startswith(old_title):
        raise SystemExit("unexpected manuscript title")

    front_matter = f"""# {TITLE}

Amirreza Rezaee^a,*, Peyman Neamatollahi^a

^a {AFFILIATION}

*Corresponding author: LeDerouxe@gmail.com

"""
    body = front_matter + body[len(old_title):].lstrip()
    declarations = """
## CRediT authorship contribution statement

Author confirmation required before submission. The author team must replace
this notice with an accurate CRediT contribution statement approved by both
authors.

## Funding

Author confirmation required before submission. State all financial support
for this work, including grant number(s), or state explicitly that the research
received no specific grant.

## Declaration of competing interest

Author confirmation required before submission. State either the applicable
competing interests or the authors' confirmation that they have no known
competing financial interests or personal relationships that could have
appeared to influence the work reported in this paper.

## Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

Author confirmation required before submission. Elsevier requires a transparent
declaration when generative AI or AI-assisted technology has been used in
manuscript preparation beyond basic spelling, grammar, or punctuation checks.
The author team must insert an accurate statement naming the tool, describing
the purpose of use, confirming human review and editing, and accepting full
responsibility for the submitted content.

"""
    output = body + declarations + "## References\n\n" + REFERENCES
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "jisa-submission-manuscript-en.md").write_text(output, encoding="utf-8")

    readme = f"""# JISA initial-submission package

## Manuscript identity

- Journal: *Journal of Information Security and Applications* (JISA)
- Article type: Research article
- Corresponding author: Amirreza Rezaee (`LeDerouxe@gmail.com`)
- Authors: Amirreza Rezaee; Peyman Neamatollahi
- Affiliation: {AFFILIATION}

## Included files

- `jisa-submission-manuscript-en.md`: the English manuscript packaged for JISA,
  with numerical citations and a numbered reference list.
- `cover-letter.md`: editable cover-letter draft.
- `submission-readiness.md`: the final author-confirmation and upload checklist.

## Important boundary

This package is ready for final author declarations and conversion into the
single manuscript file accepted by JISA's initial-submission workflow. It must
not be submitted while any "Author confirmation required" text remains in the
manuscript.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    cover = f"""Dear Editor,

Please consider our manuscript, \"{TITLE},\" for publication as a research
article in the *Journal of Information Security and Applications*.

The manuscript reports a controlled and reproducible empirical case study of
four TLS 1.3 migration configurations in native OpenSSL 3.5.9. It separates
configuration-level fresh-handshake behavior from migration-path compatibility
and controlled network sensitivity. The primary campaign uses randomized
batches and retained raw artifacts; separate compatibility, Windows, and
fixed-delay follow-ups are reported without pooling their measurements.

We believe the manuscript fits JISA because it addresses practical information
security and cryptographic protection in a deployed protocol context, combining
TLS configuration, implementation evidence, empirical evaluation, and
reproducibility artifacts.

The manuscript is original, has not been published previously, and is not under
consideration by another journal. All authors have approved the manuscript and
agree to its submission. [Replace this paragraph only after both authors have
personally confirmed these statements.]

The analysis code, versioned configurations, non-sensitive raw campaign data,
metadata, integrity records, figures, and manuscript source are maintained at:
https://github.com/LeDerouxe/Classical-to-Post-Quantum-Empirical-Study-of-Migration-Paths
The repository is currently private; a read-only snapshot can be provided to
the editor or reviewers on request.

Sincerely,

Amirreza Rezaee
Department of Computer Engineering, Faculty of Electrical and Computer
Engineering, Hakim Sabzevari University, Sabzevar, Iran
LeDerouxe@gmail.com
"""
    (OUT / "cover-letter.md").write_text(cover, encoding="utf-8")

    checklist = """# Final author-confirmation and upload checklist

Before submission, both authors must personally confirm each item below.

- [ ] The author order, spelling, affiliation, and corresponding-author email are correct.
- [ ] Each author meets the journal's authorship criteria and approves the final manuscript.
- [ ] The CRediT authorship contribution statement is accurate and approved.
- [ ] Funding information is accurate; if there was no funding, that fact is stated explicitly.
- [ ] The competing-interest declaration is accurate.
- [ ] The generative-AI declaration accurately reflects manuscript preparation and is included if required by Elsevier policy.
- [ ] The manuscript is original, is not under review elsewhere, and contains no third-party copyrighted material without permission.
- [ ] The private-repository availability statement and reviewer-access plan are acceptable to the author team.
- [ ] All figures, tables, captions, references, and supplementary material have been visually checked in the final PDF or Word manuscript.
- [ ] The final manuscript contains no bracketed instructions or "Author confirmation required" text.

## Upload set for JISA initial submission

1. One complete English manuscript file, including title page, abstract,
   keywords, figures, tables, declarations, and references.
2. Cover letter.
3. Supplementary material, if selected for public publication or confidential
   reviewer/editor access.
4. Any files requested by the Editorial Manager workflow at the time of upload.
"""
    (OUT / "submission-readiness.md").write_text(checklist, encoding="utf-8")
    print("JISA source package created")


if __name__ == "__main__":
    main()
