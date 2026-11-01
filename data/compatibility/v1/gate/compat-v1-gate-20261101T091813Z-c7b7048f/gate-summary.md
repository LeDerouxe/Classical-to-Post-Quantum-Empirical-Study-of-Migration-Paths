# Follow-up Study A fresh-credential gate outcome

Evidence: [`gate-evidence.json`](gate-evidence.json)

Evidence SHA-256: `e2f523322739801943ad41d0d2d146dc664758a4d499d7600fa230d4f547be19`

## Gate result

The overall mandatory gate **did not pass**. The compatibility matrix was not
run.

| Test | Client-observed result | Server credential label | Gate status |
| --- | --- | --- | --- |
| L | TLS 1.3; `TLS_AES_128_GCM_SHA256`; group `x25519`; peer key `EC`; CertificateVerify `ecdsa_secp256r1_sha256`; chain and hostname PASS | `ECDSA-P-256` | PASS |
| D | TLS 1.3; `TLS_AES_128_GCM_SHA256`; group `X25519MLKEM768`; peer key `ML-DSA-65`; CertificateVerify `mldsa65`; chain and hostname PASS | Not captured by server process | FAIL |

For D, the client completed verification and reported the expected ML-DSA-65
certificate and signature. The server process exited with status `-13`
(`SIGPIPE`) before emitting its `SERVER_RESULT`, so the harness could not
confirm its selected-credential label or server-side successful completion.
This is retained as an incomplete gate result, not a profile incompatibility
finding. No retry was performed.

## Credential identity and validity

The workflow used only the fresh compatibility credentials under the ignored
`credentials/compat-v1/` directory. Both certificates were valid at the run
timestamp and have 730-day validity periods.

| Credential | Subject / SAN | Public-key type | Validity UTC | SHA-256 |
| --- | --- | --- | --- | --- |
| ECDSA | `CN=ecdsa.localhost` / `DNS:ecdsa.localhost` | `id-ecPublicKey` (P-256) | 2026-11-01 09:14:33 to 2028-10-31 09:14:33 | `233f387a63eb61a25e720b4dee96f572727f37e04c0ac8b828dcae5c330896ec` |
| ML-DSA | `CN=mldsa.localhost` / `DNS:mldsa.localhost` | `ML-DSA-65` | 2026-11-01 09:14:33 to 2028-10-31 09:14:33 | `f7ddad4d20698058efd4c9fa542162a5c9f02e61488c43d4287a014b9cf628fc` |

Combined D trust bundle SHA-256:
`55ee4e6e57818379ca173088754bd376e4bcef4ba554542ade9903beacb46964`.
The bundle and credentials are ignored and were not committed.

The pinned OpenSSL source commit and executable/library identity guards passed.
The evidence's before/after tracked-file manifests match, including both
earlier gate attempts and all earlier study artifacts. Historical credentials
were not used or overwritten. No matrix attempt was started.
