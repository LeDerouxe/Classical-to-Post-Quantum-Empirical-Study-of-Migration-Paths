# Manuscript Results Audit

**Status: PASS.** This audit was generated from immutable campaign CSVs, the compatibility attempt record, the current Results section, and both main-draft Results sections.

## Checks

- Primary Ubuntu measured rows: 600; computed medians: S0 0.833590 ms, S2 0.989207 ms, S3 1.436328 ms, S4 1.311615 ms.
- Windows measured rows: 600; computed medians: S0 1.439300 ms, S2 1.783200 ms, S3 2.087950 ms, S4 1.911900 ms.
- Network measured rows: 3000; conditions: rtt-000ms, rtt-001ms, rtt-010ms, rtt-050ms, rtt-100ms; every non-S0 median contrast was positive in all five observed batches per condition.
- Compatibility attempts: 48; successes: 36; retained failures: 12, all `NO_COMMON_GROUP`.
- English and Persian main-draft result tables contain the audited primary, Windows, network, and compatibility values.
- Required main and supplementary figure assets are present.

## Result

- No discrepancies found.
