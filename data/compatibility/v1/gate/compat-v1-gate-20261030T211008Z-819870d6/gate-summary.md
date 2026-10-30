# Follow-up Study A corrective gate outcome

Evidence: [`gate-evidence.json`](gate-evidence.json)

Evidence SHA-256: `33437f3ab1f9f30337a9de10d9da30edfa83d35d6ee1ae9f129a27050f19508c`

## Outcome

The corrective gate did not pass, so no compatibility matrix was run.

| Test | Expected selection | Handshake result | Verification result |
| --- | --- | --- | --- |
| L | ECDSA-P-256 | Failed during server-certificate verification; server received TLS alert 45 (`certificate expired`) | Not completed |
| D | ML-DSA-65 | Failed during server-certificate verification; server received TLS alert 45 (`certificate expired`) | Not completed |

Neither test emitted a completed `CLIENT_RESULT` or `SERVER_RESULT`, so the
negotiated TLS fields and selected credential label are unavailable in this
attempt. This failed gate is not a profile compatibility result.

Independent read-only inspection of the existing local certificates showed
that both had expired before this attempt:

- ECDSA test certificate: `notAfter=Oct 25 06:19:55 2026 GMT`
- ML-DSA test certificate: `notAfter=Oct 25 06:19:57 2026 GMT`

The corrected OpenSSL identity guard passed: executable and loaded library
both reported OpenSSL 3.5.9; `ldd` resolved `libssl` and `libcrypto` from the
pinned installation. The ignored D trust bundle SHA-256 was
`08697dc63348575ad27561ab457fbd775b8ee90ffb7f66603c6169f8c268e805`.

The historical tracked-file SHA-256 manifests match. They include the first
failed-gate attempt. No prior gate evidence or other Phase 0–2B/final artifact
was changed. No matrix attempt was started.
