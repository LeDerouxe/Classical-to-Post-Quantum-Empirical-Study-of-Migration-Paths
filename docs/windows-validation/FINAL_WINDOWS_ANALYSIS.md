# Final Windows Validation Analysis

## Scope and data provenance

This analysis concerns Windows campaign
`campaign-20261109T081504Z-c825d34051ff` only. It used the same physical Intel
Core i5-12450H as the Ubuntu primary campaign, but it is a distinct campaign
and its observations are not pooled with Ubuntu observations. Collection used
the native Windows OpenSSL 3.5.9 build from source commit
`45e844fa2a14ec92d146bd8f5778ac130b6625fb`.

The analysis script is `scripts/analysis/analyze_windows_campaign.py`. It
validates the raw CSV hashes against campaign metadata, writes derived outputs
only below the ignored `data/processed/` tree, and does not alter raw files.

## Integrity and inclusion rule

- Five completed batches produced 800 rows: 200 retained warm-ups and 600
  measured fresh handshakes.
- The analysis includes all 600 measured rows, or 150 observations per case.
- Every one of the 800 rows passed client/server process-return, TLS 1.3,
  cipher, group, authentication, chain, hostname, and affinity validation.
- AC was online and the `High performance` power scheme was recorded before
  and after every batch. The processes used distinct performance-class cores.
- No observation or completed batch was removed. The 1.5 x IQR counts are
  descriptive only.

## Analysis method

The endpoint is the QueryPerformanceCounter duration around client
`SSL_connect()`, reported in milliseconds. Medians and IQRs are primary
summaries; mean, standard deviation, CV, P95, and P99 are descriptive
diagnostics. Each 95% percentile bootstrap CI uses 20,000 resamples that first
resample the five batches and then observations within selected batches.
Because there are only five batches, the intervals describe uncertainty and
are not used for null-hypothesis claims.

`S0 contrast` is median(case) minus median(S0). The contrast intervals are
batch-paired: a resample selects the same batch positions for S0 and the
candidate case before separately resampling their observations.

## Within-Windows latency results

| Case | n | Median ms | Primary 95% CI | IQR ms | 1.5 x IQR outliers | S0 contrast ms | Primary contrast 95% CI |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| S0 | 150 | 1.439 | [1.411, 1.470] | 0.189 | 11 | 0.000 | [0.000, 0.000] |
| S2 | 150 | 1.783 | [1.735, 1.851] | 0.211 | 14 | +0.344 | [+0.294, +0.406] |
| S3 | 150 | 2.088 | [1.955, 2.227] | 0.580 | 8 | +0.649 | [+0.507, +0.788] |
| S4 | 150 | 1.912 | [1.819, 2.055] | 0.548 | 8 | +0.473 | [+0.369, +0.631] |

Every non-classical configuration had a larger median than S0. The direction
was positive in every batch: S2 ranged from +0.309 to +0.399 ms, S3 from
+0.507 to +0.826 ms, and S4 from +0.366 to +0.721 ms. The pooled median
ordering was S0, S2, S4, then S3. This ordering is descriptive; the analysis
does not claim that the gap between S3 and S4 is stable in every batch.

S4 contained the largest retained maximum (12.457 ms) and the highest
descriptive CV (47.4%). It remains included under the prespecified retention
rule. Its positive S0 contrast was nevertheless observed in all five batches.

## Interpretation boundary

The result supports a direction check for the within-platform contrasts under one
Windows 11 build, one device, one OpenSSL build, loopback transport, and local
credentials. It neither estimates Windows-minus-Ubuntu absolute-time effects
nor does it generalize to other systems, networks, browsers, public PKI, or
production workloads.
