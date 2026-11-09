# Windows final campaign integrity record

## Scope

This record covers the completed Windows validation campaign
`campaign-20261109T081504Z-c825d34051ff`. It is the Step 4, same-device
cross-platform validation specified in the Windows protocol. It is not pooled
with the Ubuntu primary campaign and does not support a general comparison of
operating systems.

The campaign used the native Windows OpenSSL 3.5.9 build from source commit
`45e844fa2a14ec92d146bd8f5778ac130b6625fb`, TLS 1.3 only, and
`TLS_AES_128_GCM_SHA256` only. The metadata records OpenSSL, environment,
credential, source, and repository identities in full.

## Collection result

All five batches completed once. There was no retry, resume, or rerun.

| Item | Result |
| --- | --- |
| Fresh handshakes | 800 / 800 successful and configuration-valid |
| Retained warm-ups | 200 |
| Measured handshakes | 600 |
| Measured observations per case | 150 each for S0, S2, S3, and S4 |
| Client/server CPU affinity | logical processors 3 and 4; distinct performance-class physical cores |
| AC and power scheme | AC online; `High performance` before and after every batch |
| Campaign status | `complete` |

The preflight selected the two active, non-sibling processor sets with the
highest reported Windows efficiency class. The native client and server each
reported the requested affinity mask for every retained row. Every row passed
TLS-version, cipher, group, authentication, certificate-chain, and hostname
checks.

This is an integrity record only. It reports no latency comparison or
cross-platform conclusion.

## Immutable artifact inventory

| Batch | CSV | SHA-256 |
| --- | --- | --- |
| b01 | `data/raw/windows/campaign-20261109T081504Z-c825d34051ff/campaign-20261109T081504Z-c825d34051ff-b01.csv` | `29b42bc16256a837660cba3e75e2922343bc7cb5513f8ea0fa9f6564090a71f5` |
| b02 | `data/raw/windows/campaign-20261109T081504Z-c825d34051ff/campaign-20261109T081504Z-c825d34051ff-b02.csv` | `0b2453db92e94c7166f595d290510cd4a441fbc2487fcec67b1b882eb8718705` |
| b03 | `data/raw/windows/campaign-20261109T081504Z-c825d34051ff/campaign-20261109T081504Z-c825d34051ff-b03.csv` | `94feb4bc41ad62cf0ea8a2fb13463e5ff0895c68399abecdd45cf090cc4ed2ee` |
| b04 | `data/raw/windows/campaign-20261109T081504Z-c825d34051ff/campaign-20261109T081504Z-c825d34051ff-b04.csv` | `0bd62b311d0681d8e44807a7898c7995c0a1812a19e80ab89dc3aa850c454c67` |
| b05 | `data/raw/windows/campaign-20261109T081504Z-c825d34051ff/campaign-20261109T081504Z-c825d34051ff-b05.csv` | `adf303f824f3683458375144d590c7d2cd62d4186fac811f969e292a62b51814` |

The campaign metadata file is
`data/metadata/windows/campaign-20261109T081504Z-c825d34051ff/campaign-20261109T081504Z-c825d34051ff.json`;
its SHA-256 is
`649183d771ba374b302d0b94e809dc59b34a84771e392443b152d1204b722d33`.

The successful preflight and smoke evidence files are respectively
`evidence/windows-final-workflow/preflight-20261109T081441Z.json`
(`31e7f87cf9117cbfd73c069089bdb75c1499939a173c105ef9bb00e81f02605d`)
and `evidence/windows-final-workflow/smoke-test-20261109T081452Z.json`
(`eda0795f6ed2183842907e8cfae480c4ee1118e4810eed0e3769b0ef57e5a75f`).
