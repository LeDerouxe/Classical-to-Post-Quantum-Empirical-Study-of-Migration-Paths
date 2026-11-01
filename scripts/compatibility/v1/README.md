# Follow-up Study A compatibility workflow v1

This directory contains the separate, versioned native OpenSSL workflow for
the approved profile compatibility protocol. It implements the mandatory
dual-certificate capability gate and the separately implemented 4×4
functional compatibility matrix. The gate and matrix produce distinct,
immutable evidence records. Neither is a performance experiment.

## Fixed identity and controls

- Protocol: [`docs/phase-4/PROFILE_COMPATIBILITY_PROTOCOL.md`](../../../docs/phase-4/PROFILE_COMPATIBILITY_PROTOCOL.md)
- OpenSSL source: 3.5.9 commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb`
- TLS: TLS 1.3, `TLS_AES_128_GCM_SHA256`
- Fresh client/server processes per gate test. TLS session tickets are
  intentionally disabled for this fresh, one-shot compatibility gate, and
  session resumption is outside its scope; the session cache is also off.
- All four profile definitions are in
  [`configs/compatibility/v1/profiles.json`](../../../configs/compatibility/v1/profiles.json).
- Compatibility-only test keys/certificates live under the ignored
  `credentials/compat-v1/` directory; historical credentials remain unused and
  untouched. The workflow refuses handshakes unless both certificates have
  the expected public-key type and SAN hostname, are currently valid, and span
  at least 365 days.
- L trusts only the ECDSA test root. D uses a combined local CA bundle made
  from both compatibility-only test roots; the ignored bundle's SHA-256 is
  recorded in gate evidence.
- No power setting is changed.

## Native dual-certificate gate

`tls_compat_gate.c` creates one native `SSL_CTX` per one-accept server process,
loads both local credential pairs, and registers `SSL_CTX_set_cert_cb`. The
callback inspects the actual peer `signature_algorithms` list through
`SSL_get_sigalgs`: an offered `mldsa65` scheme selects ML-DSA-65; otherwise an
offered `ecdsa_secp256r1_sha256` selects ECDSA P-256. No separate
single-certificate server configuration is used.

The workflow runs the pinned `openssl` executable with the install's pinned
`LD_LIBRARY_PATH`, records the executable and library versions, and refuses
the gate unless both report OpenSSL 3.5.9 and the executable resolves `libssl`
and `libcrypto` from the pinned install.

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

## Matrix workflow

`tls_compat_matrix.c` and `run_matrix.py` implement the protocol's ordered
client-profile × server-profile matrix. Before any attempt, the runner checks
the pinned OpenSSL source commit, executable and loaded-library versions,
`libssl`/`libcrypto` linkage, ignored compatibility credential files, each
certificate's subject, SAN, key type/curve and current validity, and that the
combined D trust bundle exactly contains the two compatibility roots. It also
compiles the harness with warnings treated as errors and records host context
without requiring performance mode or changing power settings.

Each fresh attempt applies the client and server profiles' configured group
and signature lists at their respective endpoints. L/H servers present only
ECDSA credentials, Q servers only ML-DSA, and D servers use one native
`SSL_CTX` with the capability-based certificate callback. TLS 1.3,
`TLS_AES_128_GCM_SHA256`, disabled session cache and zero TLS 1.3 tickets are
fixed. The actual negotiated group is recorded; the runner does not assume a
group as a success criterion. Success requires a completed TLS handshake plus
passing chain and hostname validation. Failed attempts are retained and are
never retried.

The collection command is:

```sh
python3 scripts/compatibility/v1/run_matrix.py
```

Run it once only. It records a 64-bit master seed, shuffles all 16 ordered
pairs × 3 repetitions into one 48-attempt schedule, and creates a unique
campaign directory under `data/compatibility/v1/matrix/`. Existing campaign
directories are never reused. A campaign contains the immutable `attempts.csv`,
`metadata.json`, a factual 4×4 `outcome-report.md`, and an `integrity.json` with
SHA-256 values and historical tracked-file manifest comparison. Matrix results
are local native-OpenSSL compatibility evidence only; they are not browser,
public-PKI, Internet, or production interoperability evidence. The workflow
does not measure latency, CPU use, bytes, packets, or performance comparisons.
