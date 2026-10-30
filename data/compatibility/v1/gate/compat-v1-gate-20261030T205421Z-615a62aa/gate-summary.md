# Follow-up Study A dual-certificate gate outcome

Gate evidence: [`gate-evidence.json`](gate-evidence.json)

Evidence SHA-256: `bc6f87630d6b9f8a5a2064eae17dfeb584e4cc0d824773bdbd4f7b350ad119f0`

## Outcome

The mandatory gate **failed**. Both fresh loopback tests reached the server's
certificate callback, but it reported
`no_supported_client_signature_capability`; OpenSSL then returned a TLS
internal-error alert. Neither handshake completed, neither server credential
was selected, and no credential type was delivered to either client. The
callback implementation therefore did not demonstrate the required
capability-based selection.

| Test | Client profile | Selected credential | TLS result | Certificate/hostname validation |
| --- | --- | --- | --- | --- |
| L | ECDSA-only, `x25519` | None | Failed in server certificate callback; client received TLS alert 80 | Not reached |
| D | ECDSA + ML-DSA, `X25519MLKEM768:x25519:MLKEM768` | None | Failed in server certificate callback; client received TLS alert 80 | Not reached |

TLS version, cipher, group, peer public-key type, and CertificateVerify scheme
were not negotiated and are consequently unavailable for both tests. This is
recorded as a gate failure, not as evidence of profile incompatibility.

## Identity and environment

The attempted harness was compiled with the pinned source headers and linked
to `third_party/openssl-3.5.9/install/lib/libssl.so.3` and `libcrypto.so.3`,
as shown in the evidence's `ldd` output. The OpenSSL source checkout was
`45e844fa2a14ec92d146bd8f5778ac130b6625fb`.

The evidence's `openssl version -a` subprocess reported a system-library
version of 3.5.5 because that command was launched without the install's
`LD_LIBRARY_PATH`. A direct version check with the pinned library path set
reported OpenSSL 3.5.9 for both executable and library. The linked harness
itself resolved to the pinned install.

The captured environment snapshot is in the JSON evidence. At gate time AC,
power profile, platform profile, and EPP reported online/performance, while
CPU frequency governors reported `powersave`. This workflow did not change
system power settings.

No compatibility matrix was run. The prior tracked files' before/after SHA-256
manifests match exactly (`historical_tracked_files_unchanged: true`).
