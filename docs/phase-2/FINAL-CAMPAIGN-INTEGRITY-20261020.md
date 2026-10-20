# Final Ubuntu Campaign — Integrity Report

## Campaign record

- Campaign ID: `campaign-20261020T083014Z-70543371b61f`
- Repository commit used: `1e596dd32804a909025ba4b4888135d76dcb580c`
- OpenSSL: `3.5.9`; source commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb`
- Result: all five batches completed; no batch was resumed or rerun.
- Dataset totals: 800 rows, comprising 200 warm-ups and 600 measured handshakes. Each case has 150 measured observations.

## Batch files and integrity checks

| Batch | Raw CSV | Metadata JSON | SHA-256 (CSV) | Rows (warm-up / measured) | Handshake outcomes | Configuration | Start / end guards |
|---|---|---|---|---:|---|---|---|
| b01 | `data/raw/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b01.csv` | `data/metadata/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b01.json` | `19fcaabbdf50fd2d7ad2aeec18280aa7fc61cbae2e80c6a13adb9f25428ed4b5` | 160 (40 / 120) | 160 success, 0 failure | PASS | PASS / PASS |
| b02 | `data/raw/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b02.csv` | `data/metadata/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b02.json` | `d1176e04151765c67a518e40277b7c8dbeff2a2da3e75d84b91438c71be8c568` | 160 (40 / 120) | 160 success, 0 failure | PASS | PASS / PASS |
| b03 | `data/raw/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b03.csv` | `data/metadata/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b03.json` | `bba09eb79d1298507bd0f5d27f7f555facaa59312023974de3e3da0b63be3a8e` | 160 (40 / 120) | 160 success, 0 failure | PASS | PASS / PASS |
| b04 | `data/raw/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b04.csv` | `data/metadata/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b04.json` | `96e99e102bc74ecd9b1f9be35905cc43ac59513e19d6a537d022ac7b34d5236c` | 160 (40 / 120) | 160 success, 0 failure | PASS | PASS / PASS |
| b05 | `data/raw/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b05.csv` | `data/metadata/final/campaign-20261020T083014Z-70543371b61f/campaign-20261020T083014Z-70543371b61f-b05.json` | `ad01a94d9ffe18702a413c89b4fc816beea68742c5646fbe398f48ca9100abf2` | 160 (40 / 120) | 160 success, 0 failure | PASS | PASS / PASS |

Each batch contains 10 warm-ups and 30 measured handshakes for each of S0, S2, S3, and S4. Across the campaign, every case has 50 warm-up successes, 150 measured successes, and zero failures. The measured order in every batch matches its recorded seeded randomized order.

| Case | Warm-up successes | Measured successes | Measured failures | Measured observations |
|---|---:|---:|---:|---:|
| S0 | 50 | 150 | 0 | 150 |
| S2 | 50 | 150 | 0 | 150 |
| S3 | 50 | 150 | 0 | 150 |
| S4 | 50 | 150 | 0 | 150 |

Configuration validation passed for all 800 rows: negotiated TLS version `TLSv1.3`, cipher `TLS_AES_128_GCM_SHA256`, group and signature matched the case configuration, and client-side TCP_INFO byte and packet counters were present and positive.

For both the pre-batch and post-batch snapshots of all five batches, guards passed: AC was online; power and platform profiles were `performance`; every CPU policy reported governor and EPP `performance`; CPUs 2 and 4 were online, distinct non-sibling P-cores; and CPU 0 remained available to the OS. The required 120-second idle interval was recorded between completed batches.

## Prior-artifact integrity

No existing Phase 0, Phase 1, Phase 2, or Phase 2B artifact changed. The only support-file change was adding a Git attribute to preserve final raw CSV bytes; this report is new, and the campaign outputs use separate paths. Key Phase 2/2B SHA-256 checks remained:

- Original Phase 2 CSV: `d9e2363a8bc26b735094c490bb2d026198edbfbd91a25ddb87f8346632c30cc0`
- Original Phase 2 report: `1abb380cb55fdde8028536f83c23ad816f692cbe5219d033a95cdcac3227db62`
- Phase 2B CSV: `016b3e73e25a9403b03b246984aa83b66d5873052b974756fd973784a881397d`
- Phase 2B report: `f3c7e18dce8994e98e844634334f03aadd94d0a71bb9683ca390bed0f1d52099`
- Phase 2B metadata: `e2160d593e1ac95b434fd1e353b5d6e49ef672d4bed609b1ad48cbfc01420a49`
- Phase 2B approved-policy/preflight metadata: `6d34c45ff91c36dde178d6e0d822579035a60ae7e2eda90d37f607a8b4246026`
- Phase 2B stabilization protocol: `1ec63ed72e455a2bd49ce2dd521966afccc4605e76a13a5ec2d0dd05b4482666`

No performance summaries, comparisons, rankings, averages, or conclusions are included in this report.
