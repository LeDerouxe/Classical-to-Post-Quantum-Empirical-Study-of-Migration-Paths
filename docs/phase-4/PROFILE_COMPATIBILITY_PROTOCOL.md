# Follow-up Study A — Migration-Profile Compatibility Protocol

## Purpose and status

**Status: approved design; collection has not started.** This functional study
tests whether defined client and server migration profiles negotiate TLS 1.3,
what they negotiate, and whether a transition profile retains a classical
fallback. It is separate from the final Ubuntu performance campaign: it is not
a latency benchmark and makes no browser, public-PKI, or production claim.

Forced S0-by-S4 pairings would mostly document predictable failures from
mutually exclusive settings. This profile-based design instead tests plausible
staged-deployment behavior.

## Fixed environment and controls

- Native Ubuntu 26.04.1; pinned OpenSSL 3.5.9 source commit
  `45e844fa2a14ec92d146bd8f5778ac130b6625fb`; existing fresh-process loopback
  harness.
- TLS 1.3 only; `TLS_AES_128_GCM_SHA256`; tickets, resumption, and session
  cache disabled; fresh client and one-accept server in every attempt.
- Ignored local ECDSA P-256 and ML-DSA-65 test credentials only; profiles
  trust the appropriate local test roots. No credentials are committed.
- Record OpenSSL identity, repository commit, topology, AC/power/governor/EPP
  state, and complete profile configuration. The workflow must not alter power
  settings.
- Use a unique immutable compatibility-campaign directory. Retain every
  success, failure, metadata file, and SHA-256 checksum. Never mix these files
  with primary performance CSVs.

## Profiles

| ID | Role | Groups | Authentication capability |
| --- | --- | --- | --- |
| L | Legacy | `x25519` | ECDSA P-256 only |
| H | Hybrid-key-establishment transition | `X25519MLKEM768:x25519` | ECDSA P-256 only |
| D | Dual-capable transition | `X25519MLKEM768:x25519:MLKEM768` | Client accepts ECDSA P-256 and ML-DSA-65; server dynamically selects ECDSA P-256 or ML-DSA-65 from client capability. |
| Q | Strict PQ | `MLKEM768` | ML-DSA-65 only |

The ordered group lists are preferences, not assumed selection behavior. The
harness records configured lists verbatim and observed negotiation. RFC 10024
defines `X25519MLKEM768` as hybrid; `MLKEM768` here is only the
implementation-supported pure-PQ group of the pinned build.

## Mandatory dual-certificate gate

Before the matrix, one native-OpenSSL dual-certificate server context must pass
both tests:

1. An L client completes a fresh handshake and validates the ECDSA certificate
   and CertificateVerify signature.
2. A D client completes a fresh handshake and validates the ML-DSA certificate
   and CertificateVerify signature.

Both records must include TLS version, cipher, group, peer public-key type,
CertificateVerify scheme, hostname/chain result, and selected server credential
label. The behavior must use native OpenSSL APIs in the harness; running a
different single-certificate server per client is not a substitute. If either
test fails, or both select the same authentication material, retain evidence,
report the limitation, and do **not** run the matrix as a transition result.

## Matrix after a passed gate

Run every ordered client/server pair of L, H, D, Q three times with a recorded
randomized order: 16 pairs × 3 = 48 independent fresh attempts. Repetition is
only an implementation-stability check, not performance sampling.

For every attempt record campaign/attempt IDs, sequence index, client and
server profile, exact configured lists, success/failure with sanitized error,
TLS version, cipher, negotiated group, peer certificate public-key type,
CertificateVerify scheme, verification result, selected server credential,
timestamps, commit/OpenSSL identity, and environment snapshots. A TCP
connection alone is never a success.

## Interpretation and completion

A success documents only the recorded local native-OpenSSL profiles and test
credentials. A failure is retained with its configuration evidence; it is not
silently retried nor generalized as an algorithm failure. No latency, CPU,
packet, or byte comparison is derived.

Completion requires versioned harness/config changes and README; gate evidence;
matrix CSV/metadata/checksums; and a factual 4-by-4 outcome report with
selected parameters, failure categories, and these limitations.
