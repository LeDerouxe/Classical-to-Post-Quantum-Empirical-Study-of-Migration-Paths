# Phase 2 Pilot Report

## Run identity

- Run ID: `pilot-20261018T100351Z-e2a007cf`
- Collection commit: `442b65ffd0adfcdd0da2a2eec5bc0993fe53800a`
- OpenSSL: 3.5.9, source commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb`
- Configurations: S0, S2, S3, and S4; all completed successfully.
- Collection: 10 warm-ups and 30 measured fresh handshakes per case; measured sequence randomized across cases.
- Raw CSV: `data/raw/pilot/pilot-20261018T100351Z-e2a007cf.csv` (60,890 bytes)
- Metadata: `data/metadata/pilot/pilot-20261018T100351Z-e2a007cf.json`
- CSV SHA-256: `d9e2363a8bc26b735094c490bb2d026198edbfbd91a25ddb87f8346632c30cc0`

## Data-quality checks

- 160 CSV rows: 40 warm-ups and 120 measured observations; 30 measured rows per case.
- All 160 handshakes succeeded. TLS 1.3, `TLS_AES_128_GCM_SHA256`, requested group, and requested signature scheme matched in every row.
- The measured sequence had 91 adjacent case changes across 120 observations, consistent with the recorded randomized interleaving.
- Byte and segment counters use client-side `TCP_INFO`; the method was validated against loopback packet captures for all four configurations before this run. Packet capture was not active during pilot measurement.
- The CSV SHA-256 matches the run metadata. The raw CSV is stored read-only and is committed unchanged.

## Preliminary variance observations

These describe spread within this one pilot run only. They are not performance conclusions.

| Case | n | TLS handshake latency range (ms) | Standard deviation (ms) | Coefficient of variation |
|---|---:|---:|---:|---:|
| S0 | 30 | 1.741–2.473 | 0.206 | 9.7% |
| S2 | 30 | 2.152–7.839 | 1.020 | 35.7% |
| S3 | 30 | 2.743–11.054 | 2.015 | 43.2% |
| S4 | 30 | 2.452–9.874 | 1.691 | 40.4% |

The observed spread, particularly the high within-case variation in S2/S3/S4, warrants review of measurement stability and variance sources before drawing conclusions. This report does not interpret the differences between cases. Do not start Phase 3 until the pilot has been reviewed and explicitly accepted.
