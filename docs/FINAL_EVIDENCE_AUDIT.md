# Final Evidence Audit

## Purpose

This audit maps each research question to its immutable evidence, the narrow
claim supported by that evidence, and the limit that must accompany the claim.
It does not perform a new statistical analysis or change raw data.

## Evidence map

| Research question | Evidence | Supported result | Required limit |
| --- | --- | --- | --- |
| RQ1: configuration effects | Ubuntu loopback campaign `campaign-20261020T083014Z-70543371b61f`; five batches; 600 measured handshakes | All three non-classical cases had positive median latency contrasts relative to S0 in all five batches. Communication and resource descriptors were recorded for the same harness boundary. | One Ubuntu/OpenSSL loopback case study; no external-network, browser, production, or universal performance claim. |
| RQ2: migration path and compatibility | Migration-change record; dual-certificate gate; 4-by-4 native OpenSSL matrix with 48 attempts | The defined D profile bridged L/H and Q in this local OpenSSL implementation. Twelve failures were retained as no-common-group outcomes. | No public-PKI, browser, Internet, or deployment-interoperability claim. The record does not measure human migration effort. |
| RQ3: controlled network sensitivity | Network campaign `campaign-20261114T202013Z-44a824c91fb9`; five RTT conditions; 3,000 measured handshakes | At 10, 50, and 100 ms added RTT, S2 remained close to S0, while S3/S4 had median contrasts close to one added RTT. Every non-S0 contrast was positive in every condition-specific batch. | Fixed symmetric delay only. No loss, jitter, congestion, bandwidth cap, public Internet, or causal network-mechanism claim. Conditions are not pooled. |
| RQ4: cross-platform direction validation | Windows campaign `campaign-20261109T081504Z-c825d34051ff`; five batches; 600 measured handshakes | S2, S3, and S4 had positive S0 contrasts in every Windows batch, matching the Ubuntu direction. | No pooled dataset, absolute Windows-minus-Ubuntu comparison, or operating-system effect estimate. |

## Cross-cutting controls

- OpenSSL source commit was pinned to
  `45e844fa2a14ec92d146bd8f5778ac130b6625fb` for the Ubuntu and Windows
  performance campaigns.
- Primary, Windows, and network campaigns used fresh client and server
  processes, TLS 1.3, and `TLS_AES_128_GCM_SHA256`.
- Completed campaigns retain raw CSVs, per-batch metadata, recorded
  environment checks, and SHA-256 integrity checks.
- Analyses retain all protocol-defined measured observations and completed
  batches. Bootstrap intervals are uncertainty descriptions with five batches,
  not null-hypothesis tests.

## Non-combinability rule

The Ubuntu loopback, network-sensitivity, and Windows datasets differ in
transport topology or timing environment. They must be summarized within their
own studies. No pooled estimate is used to claim a platform, network, or
deployment effect.

## Manuscript-release check

Before release, each empirical statement in the abstract, results, discussion,
and conclusion must be traceable to one row of this audit and retain its stated
limit.
