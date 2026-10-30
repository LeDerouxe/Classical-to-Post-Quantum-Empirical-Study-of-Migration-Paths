# Follow-up Study A compatibility workflow v1

This directory contains the separate, versioned native OpenSSL workflow for
the approved profile compatibility protocol. It implements the mandatory
dual-certificate capability gate only. It does not implement or collect the
4×4 matrix as part of this work.

## Fixed identity and controls

- Protocol: [`docs/phase-4/PROFILE_COMPATIBILITY_PROTOCOL.md`](../../../docs/phase-4/PROFILE_COMPATIBILITY_PROTOCOL.md)
- OpenSSL source: 3.5.9 commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb`
- TLS: TLS 1.3, `TLS_AES_128_GCM_SHA256`
- Fresh client/server processes per gate test; tickets and session cache off.
- All four profile definitions are in
  [`configs/compatibility/v1/profiles.json`](../../../configs/compatibility/v1/profiles.json).
- Test keys/certificates must already exist locally under `credentials/`; no
  credential is generated, copied, or committed by this workflow.
- No power setting is changed.

## Native dual-certificate gate

`tls_compat_gate.c` creates one native `SSL_CTX` per one-accept server process,
loads both local credential pairs, and registers `SSL_CTX_set_cert_cb`. The
callback inspects the actual peer `signature_algorithms` list through
`SSL_get_sigalgs`: an offered `mldsa65` scheme selects ML-DSA-65; otherwise an
offered `ecdsa_secp256r1_sha256` selects ECDSA P-256. No separate
single-certificate server configuration is used.

The client tests are exactly:

1. L client: `x25519`, ECDSA-only; validates the ECDSA server certificate,
   hostname, and CertificateVerify.
2. D client: `X25519MLKEM768:x25519:MLKEM768`, ECDSA plus ML-DSA; validates
   the ML-DSA server certificate, hostname, and CertificateVerify.

Each result records the observed TLS version, cipher, group, peer public-key
type, CertificateVerify signature scheme, chain and hostname verification,
server-selected credential label, process output, pinned OpenSSL identity,
repository commit, and a host environment snapshot. The record also captures
before/after hashes for files present at the workflow's starting commit to
check preservation of prior tracked artifacts.

## Run the gate

From the repository root, with the pinned OpenSSL install and ignored local
credentials available:

```sh
python3 scripts/compatibility/v1/run_gate.py
```

This compiles the native harness into a unique evidence directory and runs only
the two gate connections. It writes a new immutable JSON evidence record and a
SHA-256 sidecar under `data/compatibility/v1/gate/`. Failed attempts are kept
there; rerunning creates a new evidence directory. The program never starts
the 48-attempt compatibility matrix. Inspect both test results and the
top-level `gate_passed` field before any later matrix work is considered.
