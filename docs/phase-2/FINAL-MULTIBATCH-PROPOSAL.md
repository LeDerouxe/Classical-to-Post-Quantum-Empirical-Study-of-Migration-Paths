# Final Multi-Batch Measurement Design — Proposal

**Status: proposed for review; not approved and not executed.** This document is a design only. It authorizes no data collection and makes no performance conclusion. Preserve all existing Phase 2 and Phase 2B artifacts as collected.

## Proposed scope and controls

- Native Ubuntu loopback only; cases S0, S2, S3, and S4, using the existing C harness and pinned OpenSSL 3.5.9 build.
- Five separate batches. In every batch, collect 30 measured fresh handshakes per case (150 per case overall; 600 measured observations total), plus 10 warm-up handshakes per case (200 warm-ups overall). Warm-ups are flagged and excluded from analysis.
- Within each batch, randomize the order of the four case blocks using a recorded, reproducible seed. Keep each case's 30 measured handshakes together within its block so batch-level environmental snapshots remain interpretable. Randomize block order independently for each batch; record the realized order and seed.
- Pin client to CPU 2 and server to CPU 4, after rechecking topology confirms these are distinct, non-sibling P-cores. Keep CPU 0 available to the OS. Abort before collection if this mapping is no longer valid.
- Hold AC connection, system performance profile, CPU governor, and EPP at the Phase 2B approved `performance` settings for all batches. Do not change the policy during this proposed measurement. If AC or any policy state deviates, stop the batch, preserve any partial output as an incomplete immutable run, and document the deviation; do not silently resume it as a valid batch.
- Keep the existing TLS 1.3, cipher, requested group/signature/certificate, fresh-handshake, resumption-disabled, timing-boundary, and TCP_INFO instrumentation controls from the reviewed C harness protocol.

## Batch artifacts and drift metadata

Use a unique immutable CSV and metadata JSON for each batch; never append to or overwrite a completed file. Each measured row must carry a `batch_id`, case, sequence/order index, warm-up flag, UTC timestamp, handshake outcome, and all current raw timing/resource/network fields. Retain failed handshakes and their error reasons.

For every batch, capture environment snapshots immediately before the first warm-up and immediately after the final measured handshake. Record both snapshot timestamps and batch start/end UTC timestamps, elapsed duration, planned and realized case order, random seed, host/repository commit, OpenSSL version/source commit, CPU topology and affinity, AC online/charging state, power profile/platform profile, per-policy governor/EPP, load average, running desktop/background activity summary, CPU frequency, and available thermal readings. Record unavailable readings explicitly as unavailable with the reason; do not infer them. Also record interruptions, pauses, policy/AC deviations, and any batch restart or incomplete termination. These fields are intended to reveal within- and between-batch environmental drift.

## Proposed analysis plan

Keep and checksum the complete raw observations, including failures and statistical outliers. Do not remove observations solely because they are outliers. Any exclusion for a separately documented instrumentation failure must retain the original row and state the predeclared reason.

For each case, summarize measured `tls_handshake_ns` by batch and across all five batches using median and IQR. Report sample counts, failures, and per-batch start/end environment changes. Estimate 95% bootstrap confidence intervals for each case's median and IQR, using a fixed recorded seed and a batch-stratified resampling procedure (resample batches, then observations within selected batches). Because there are only five batches, label these intervals as exploratory and report the bootstrap method and resample count. Include per-batch summaries and a sensitivity view that resamples observations within batches while holding batch membership fixed, so readers can see the role of between-batch drift.

If a later review explicitly authorizes comparative analysis, comparisons must be predeclared and account for batch as a blocking factor; report effect estimates and uncertainty rather than relying on rankings or p-values alone. This proposal itself contains no comparative results.

## Review gate

Before execution, review and approve this design, confirm the host and CPU mapping, confirm the pinned OpenSSL build and harness state, and confirm the fixed AC/performance/governor/EPP policy. Until that review is complete, do not run any final measurement batch or other Phase 3 collection.
