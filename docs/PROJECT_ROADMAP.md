# Project Roadmap

This roadmap separates completed evidence from planned work. A later phase does not change the scope or interpretation of an earlier one.

| Step | Work item | Status | Deliverable / decision point |
| --- | --- | --- | --- |
| 1 | Stabilize the primary dataset | Complete | The final Ubuntu campaign, its checksums, and the reproducible RQ1 analysis are fixed. Historical pilots remain diagnostic records rather than primary evidence. |
| 2 | Evidence-based drafting | In progress | The introduction, background, methodology, and RQ1 results are drafted from verified sources and recorded data. RQ2 material is now being incorporated. |
| 3 | Migration-path compatibility | Complete | The migration-change record, dual-certificate gate, and 4-by-4 local OpenSSL profile matrix are complete. The matrix contains 48 fresh attempts and is interpreted only as local implementation evidence. |
| 4 | Cross-platform validation | Collection complete; analysis pending | The Windows 11 build, performance-policy, topology/affinity, smoke, and five-batch campaign gates passed. The separate within-Windows analysis and qualitative direction comparison with Ubuntu remain. |
| 5 | Network-sensitivity study | Planned | Prepare and review a controlled `tc netem` study on Ubuntu. It will evaluate prespecified network conditions without changing the loopback findings. |
| 6 | Final analysis and figures | Planned | Integrate RQ1--RQ4 after the remaining studies, audit limitations and uncertainty, and produce the main and supplementary figures. The planned supplements include a latency-distribution/batch view and a migration-profile compatibility matrix. |
| 7 | Interpretive writing | Planned | Draft the discussion, threats to validity, conclusion, abstract, and final cross-check of every empirical and cited claim. |
| 8 | Final release | Planned | Complete reference, reproducibility, formatting, figure, and submission checks; archive the exact revision used for the manuscript. |

## Current position

Data collection and factual reporting for Step 3 are complete. Its compact matrix table and initial RQ2 reporting are now in the manuscript. No further Ubuntu collection is required for Step 3.

Steps 4 and 5 require separate protocol review before collection. They are not prerequisites for preserving or reporting the completed Ubuntu loopback results, but they are needed before making cross-platform or controlled-network claims.

## Naming note

The repository path `docs/phase-4/` is a historical storage label for
Follow-up Study A, the completed migration-profile compatibility study. It is
not Step 4 of this roadmap. Step 4 is the planned Windows 11 validation and
has not started.
