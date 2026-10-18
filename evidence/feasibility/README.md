# Phase 1 Handshake Evidence

This directory contains sanitized, client-side output for the three fresh loopback TLS 1.3 handshakes of each feasibility case.

Each file records the negotiated protocol version, cipher suite, peer certificate common name, signature type, verification result, and negotiated key-establishment group. Server logs, generated credentials, build trees, and raw operational logs are intentionally excluded from Git.

The evidence corresponds to the result table in `docs/phase-1/FEASIBILITY_RESULTS.md` and the credentials metadata in `docs/phase-1/FEASIBILITY_CREDENTIALS.md`.
