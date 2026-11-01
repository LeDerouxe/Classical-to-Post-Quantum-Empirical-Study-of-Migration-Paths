# Follow-up Study A corrective gate outcome

Campaign: `compat-v1-gate-20261101T120110Z-007ed804`

JSON evidence: [`gate-evidence.json`](gate-evidence.json)

JSON evidence SHA-256: `e0e04b843c1cd60bcc88330f4101f573a3ab8ca66849d2cfa40166686af81552`

## Identity and certificate preflight

- Repository commit used by the run: `656869783315c5c69a2cf10cb619d44ba6ccbac5`
- OpenSSL source commit: `45e844fa2a14ec92d146bd8f5778ac130b6625fb`
- The pinned executable and loaded library both reported OpenSSL 3.5.9;
  `ldd` resolved both `libssl` and `libcrypto` from the pinned installation.
- Both fresh credential preflights passed: SAN hostname, expected public-key
  type, current validity, and validity period of at least 365 days.

| Credential | Subject | SAN | Public-key type | Valid UTC | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| ECDSA P-256 | `CN=ecdsa.localhost` | `DNS:ecdsa.localhost` | `id-ecPublicKey` | 2026-11-01 09:14:33 – 2028-10-31 09:14:33 | `233f387a63eb61a25e720b4dee96f572727f37e04c0ac8b828dcae5c330896ec` |
| ML-DSA-65 | `CN=mldsa.localhost` | `DNS:mldsa.localhost` | `ML-DSA-65` | 2026-11-01 09:14:33 – 2028-10-31 09:14:33 | `f7ddad4d20698058efd4c9fa542162a5c9f02e61488c43d4287a014b9cf628fc` |

Combined compatibility-only D trust bundle SHA-256:
`55ee4e6e57818379ca173088754bd376e4bcef4ba554542ade9903beacb46964`.
Private keys, certificates, and the trust bundle remain in the ignored local
`credentials/compat-v1/` directory and are not part of this commit.

## Gate outcomes

Each row is one fresh client process and one fresh one-accept server process
using the same native dual-credential `SSL_CTX` and certificate callback.
For the server, the harness prints `SERVER_RESULT` only after `SSL_accept`
returns success; both records contain that line and both server processes
returned 0.

| Case | Client rc | Server rc | Server-selected credential | TLS | Cipher | Group | Peer key | CertificateVerify | Chain | Hostname | Outcome |
| --- | ---: | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| L | 0 | 0 | `ECDSA-P-256` | TLS 1.3 | `TLS_AES_128_GCM_SHA256` | `x25519` | `EC` | `ecdsa_secp256r1_sha256` | PASS | PASS | PASS |
| D | 0 | 0 | `ML-DSA-65` | TLS 1.3 | `TLS_AES_128_GCM_SHA256` | `X25519MLKEM768` | `ML-DSA-65` | `mldsa65` | PASS | PASS | PASS |

The prior tracked-file SHA-256 manifest comparison passed with no changed
paths. Existing gate evidence, including both failed attempts, and historical
Phase 0/1/2/2B/final-campaign artifacts remain unchanged. This gate contains
exactly the two required capability checks; `matrix_attempt_count` is 0 and
the 4×4 matrix was not run.
