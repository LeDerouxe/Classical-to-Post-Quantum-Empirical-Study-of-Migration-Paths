# Final Ubuntu Campaign Analysis

## Scope and data provenance

This analysis concerns the completed primary Ubuntu campaign
`campaign-20261020T083014Z-70543371b61f` only. It uses the five immutable
raw CSV files recorded at commit `b9da91c807d6445c7c413837d12a4a52cfeade4f`.
The collecting workflow used repository commit
`1e596dd32804a909025ba4b4888135d76dcb580c`, native OpenSSL 3.5.9, and
OpenSSL source commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb`.

The analysis script is `scripts/analysis/analyze_final_campaign.py`. It
checks the recorded CSV hashes, writes only derived files under the ignored
`data/processed/` directory, and never edits raw data.

## Integrity and inclusion rule

- Five completed batches produced 800 rows: 200 protocol-defined warm-ups
  and 600 measured handshakes.
- Analysis includes the 600 rows flagged as measured: 150 observations for
  each of S0, S2, S3, and S4.
- All 800 handshakes succeeded. TLS 1.3, cipher suite, requested group,
  requested signature, and positive client-side TCP_INFO counters matched for
  every row.
- No measured observation was removed. The 1.5 x IQR outlier counts below
  are descriptive only.

## Analysis method

The primary endpoint is client `SSL_connect()` duration, reported in
milliseconds. Medians and IQRs are reported because the distributions are
right-skewed. The primary 95% percentile bootstrap CI uses 20,000 resamples:
it resamples the five batches and then observations within selected batches.
With only five batches, those intervals describe uncertainty; they are not
used as null-hypothesis tests. A fixed-batch bootstrap sensitivity analysis,
which resamples observations while retaining membership in the five observed
batches, is also reported for the contrasts.

`S0 contrast` means the observed median for a case minus the observed median
for S0. Every configuration was compared with S0 within each batch before the
batch-aware contrast was summarized.

## Primary latency results

| Case | n | Median ms | Primary 95% CI | IQR ms | 1.5 x IQR outliers | S0 contrast ms | Primary contrast 95% CI | Fixed-batch contrast 95% CI |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- |
| S0 | 150 | 0.834 | [0.812, 0.864] | 0.114 | 7 | 0.000 | [0.000, 0.000] | [0.000, 0.000] |
| S2 | 150 | 0.989 | [0.955, 1.026] | 0.137 | 6 | +0.156 | [+0.115, +0.203] | [+0.128, +0.192] |
| S3 | 150 | 1.436 | [1.337, 1.538] | 0.642 | 5 | +0.603 | [+0.501, +0.700] | [+0.516, +0.694] |
| S4 | 150 | 1.312 | [1.219, 1.460] | 0.663 | 2 | +0.478 | [+0.383, +0.621] | [+0.398, +0.597] |

Within this native Ubuntu loopback case study, all three non-classical
configurations had higher median handshake latency than S0. The effect was
also directionally consistent in every batch: S2 contrasts ranged from
+0.116 to +0.226 ms, S3 from +0.496 to +0.653 ms, and S4 from +0.380 to
+0.546 ms.

## Communication overhead

These are client-side TCP_INFO values sampled at the completion of
`SSL_connect()`. They are TCP payload and segment counts through that
boundary; they do not include close packets or link/IP/TCP headers.

| Case | Median handshake bytes | Median packet count | Median TCP connect ms |
| --- | ---: | ---: | ---: |
| S0 | 967 | 8 | 0.045 |
| S2 | 3,231 | 8 | 0.045 |
| S3 | 11,595 | 12 | 0.045 |
| S4 | 11,531 | 12 | 0.045 |

The stable loopback connect-time medians make clear that the reported primary
latency is the TLS handshake boundary, not the preceding TCP connection.
Communication figures are configuration facts for this controlled handshake,
not estimates of external-network transfer cost.

## Resource descriptors

CPU-time medians are milliseconds within each role's documented timing
boundary. Peak RSS is a per-fresh-process maximum and is therefore a
descriptor rather than total application memory.

| Case | Client CPU median ms | Server CPU median ms | Client peak RSS KiB | Server peak RSS KiB |
| --- | ---: | ---: | ---: | ---: |
| S0 | 0.696 | 0.409 | 21,916 | 21,916 |
| S2 | 0.655 | 0.475 | 21,916 | 21,916 |
| S3 | 0.910 | 0.996 | 21,916 | 21,916 |
| S4 | 0.819 | 0.891 | 21,916 | 21,916 |

These secondary descriptors are reported without causal attribution. Their
run-level variability, especially for the PQ-authentication cases, should be
considered alongside the latency IQRs.

## Environment and limitations

Every batch began and ended with AC online; power and platform profiles,
governor, and EPP were all `performance`; and the client/server remained
pinned to non-sibling P-cores 2 and 4. The package-temperature snapshots were
43/44, 38/43, 38/43, 40/68, and 37/42 degrees C (start/end) for batches one
through five. Batch four is retained rather than discarded: its configuration
contrasts have the same direction as the other batches, and the protocol
precommitted that statistical outliers and completed batches would be kept.

These results apply to one native Ubuntu 26.04.1 loopback TLS 1.3/OpenSSL
case study. They do not establish behavior under external network conditions,
other software stacks or OpenSSL releases, Windows, other hardware, or
production application workloads.
