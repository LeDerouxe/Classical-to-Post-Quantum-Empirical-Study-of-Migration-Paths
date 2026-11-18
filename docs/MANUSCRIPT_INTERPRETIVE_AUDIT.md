# Manuscript Interpretive-Claim Audit

**Status: PASS.**

## Scope

This release check covers `manuscript/abstract.md`, Sections 8--10, and the
corresponding Discussion, Threats-to-Validity, and Conclusion material in
`manuscript/article-en.md` and `manuscript/article-fa.md`. It checks that
empirical statements are bounded by the completed evidence streams and that no
new external source claim was introduced without an evidence-matrix entry. It
does not replace the numeric Results audit.

## Claim traceability

| Manuscript location | Claim class | Evidence and bound | Result |
| --- | --- | --- | --- |
| Abstract | Ubuntu ordering and four median values | Final Ubuntu campaign; 600 measured observations; exact values are checked by `scripts/analysis/audit_manuscript_results.py`. | Pass |
| Abstract; Section 8.2; Section 10; main-draft Discussion and Conclusion | D profile bridged the evaluated profiles; 36 successes and 12 no-common-group outcomes | Local 4-by-4 compatibility matrix only; 48 retained attempts. No browser, public-PKI, or deployment-interoperability claim. | Pass |
| Abstract; Sections 8.3 and 10; main-draft Discussion and Conclusion | S3/S4 contrasts were close to one added RTT at 10, 50, and 100 ms; S2 remained close to S0 | Separate namespace/veth/netem campaign; fixed symmetric delay only; no causal-network-mechanism or Internet claim. | Pass |
| Abstract; Section 8.4; Section 10; main-draft Discussion and Conclusion | Windows reproduced the direction of the within-platform contrasts | Separate Windows campaign, five batches, 600 measured observations; no timing pooling or operating-system effect claim. | Pass |
| Sections 8--10; main-draft Discussion and Conclusion | Interpretation and practical implications | Framed as case-study interpretation, not a universal performance ranking, deployment prescription, or security-policy conclusion. | Pass |
| Section 9; main-draft Threats to Validity | Scope and validity limits | Methodology, environment metadata, and the final evidence audit; limits are stated as constraints rather than empirical findings. | Pass |

## Citation check

Sections 8--10, the abstract, and the bilingual main-draft Discussion,
Threats-to-Validity, and Conclusion sections introduce no new external
citations or literature claims. Existing manuscript citations remain governed by
`docs/citations/EVIDENCE_MATRIX.md`, whose approved wording and source bounds
were checked before insertion. Therefore this interpretive pass creates no new
citation-evidence obligation.

## Result

The abstract, discussion, threats-to-validity section, conclusion, and
bilingual main-draft Discussion, Threats-to-Validity, and Conclusion sections
preserve the non-combinability rule: Ubuntu loopback, network-sensitivity, and
Windows data are interpreted within their own study boundaries and are not
pooled.
