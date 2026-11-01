# Profile Compatibility Results

## Scope

This report summarizes Follow-up Study A. It is a functional compatibility study conducted with native OpenSSL 3.5.9 on the primary Ubuntu host. It is not a latency benchmark and does not establish browser, public-PKI, Internet, or production interoperability.

The source records are the passing dual-certificate gate and the matrix campaign `compat-v1-matrix-20261101T140752Z-7ef56e69`. The matrix CSV hash is `1e7272cc286c37b653ed41bd2f49eef215efa04cedbf338176cc4075f685ef7c`.

## Gate and matrix completion

The required gate passed before the matrix was run. With one native OpenSSL server context and its certificate-selection callback, an L client received the ECDSA P-256 credential and a D client received the ML-DSA-65 credential. Both handshakes completed TLS 1.3 verification, including certificate-chain and hostname checks.

The matrix then ran all 16 ordered client/server profile pairs three times in a recorded randomized order. Each attempt used fresh client and one-accept server processes. There were 48 attempts, 36 successes, and 12 failures; no attempt was retried.

| Client \\ Server | L | H | D | Q |
| --- | ---: | ---: | ---: | ---: |
| L | 3/3 | 3/3 | 3/3 | 0/3 |
| H | 3/3 | 3/3 | 3/3 | 0/3 |
| D | 3/3 | 3/3 | 3/3 | 3/3 |
| Q | 0/3 | 0/3 | 3/3 | 3/3 |

Every unsuccessful attempt was classified as `NO_COMMON_GROUP`. The recorded server-side error was a lack of a suitable key share. No failed attempt reached certificate or hostname verification, so these failures should be read as group-negotiation mismatches rather than authentication failures.

## Observed negotiation patterns

- L with L, H, or D negotiated `x25519` and ECDSA P-256.
- H with H or D negotiated `X25519MLKEM768` and ECDSA P-256; H with L used `x25519` and ECDSA P-256.
- D retained the ECDSA path with L and H, selected ML-DSA-65 with D, and negotiated `MLKEM768` with Q.
- Q succeeded only with D and Q, using `MLKEM768` and ML-DSA-65.

All successful attempts recorded TLS 1.3, `TLS_AES_128_GCM_SHA256`, the observed group, the expected public-key type and CertificateVerify signature, and passing chain and hostname checks.

## Interpretation boundary

Within these profile definitions and this pinned local implementation, D bridged the classical/hybrid ECDSA profiles and the strict PQ profile. That is evidence about these local native-OpenSSL configurations, not a claim that a real deployment can migrate without certificate, policy, PKI, client-population, or operational work. The study did not test those factors, fallback across arbitrary implementations, or public trust stores.
