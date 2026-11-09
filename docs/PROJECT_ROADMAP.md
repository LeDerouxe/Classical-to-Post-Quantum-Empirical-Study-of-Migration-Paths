# Project Roadmap

This roadmap separates completed evidence from planned work. A later phase does not change the scope or interpretation of an earlier one.

| Step | Work item | Status | Deliverable / decision point |
| --- | --- | --- | --- |
| 1 | Stabilize the primary dataset | Complete | The final Ubuntu campaign, its checksums, and the reproducible RQ1 analysis are fixed. Historical pilots remain diagnostic records rather than primary evidence. |
| 2 | Evidence-based drafting | In progress | The introduction, background, methodology, and RQ1 results are drafted from verified sources and recorded data. RQ2 material is now being incorporated. |
| 3 | Migration-path compatibility | Complete | The migration-change record, dual-certificate gate, and 4-by-4 local OpenSSL profile matrix are complete. The matrix contains 48 fresh attempts and is interpreted only as local implementation evidence. |
| 4 | Cross-platform validation | Complete | The separate Windows analysis and qualitative direction comparison with Ubuntu are complete. Raw observations remain unpooled and no operating-system effect is claimed. |
| 5 | Network-sensitivity study | Planned | Prepare and review a controlled `tc netem` study on Ubuntu. It will evaluate prespecified network conditions without changing the loopback findings. |
| 6 | Final analysis and figures | Planned | Integrate RQ1--RQ4 after the remaining studies, audit limitations and uncertainty, and produce the main and supplementary figures. The planned supplements include a latency-distribution/batch view and a migration-profile compatibility matrix. |
| 7 | Interpretive writing | Planned | Draft the discussion, threats to validity, conclusion, abstract, and final cross-check of every empirical and cited claim. |
| 8 | Final release | Planned | Complete reference, reproducibility, formatting, figure, and submission checks; archive the exact revision used for the manuscript. |

## Current position

Data collection and factual reporting for Steps 3 and 4 are complete. The Step 4 result corroborates the direction of the within-platform S0 contrasts on Windows, without pooling the platform datasets or estimating an operating-system effect.

Step 5 requires separate protocol review before collection. It is not a prerequisite for preserving or reporting the completed loopback findings, but it is needed before making controlled-network claims.

## Naming note

The repository path `docs/phase-4/` is a historical storage label for
Follow-up Study A, the completed migration-profile compatibility study. It is
not Step 4 of this roadmap. Step 4 is the completed Windows 11 validation.
