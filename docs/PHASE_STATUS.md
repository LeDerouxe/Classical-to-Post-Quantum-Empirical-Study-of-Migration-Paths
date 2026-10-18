# Phase Status

## Phase 0 — Environment preparation and registration

**Technical status: completed. Repository integration and pinned-build reproducibility check completed and committed on Ubuntu.**

The primary native Ubuntu 26.04.1 environment, version-pinned OpenSSL 3.5.9 build, and algorithm inventory are recorded under `environment/ubuntu-26.04.1/`.

The initial collection occurred before the Ubuntu workspace was cloned from the research repository. The integration check is recorded in the [environment manifest](../environment/ubuntu-26.04.1/environment-manifest.md).

## Phase 1 — TLS/OpenSSL feasibility validation

**Technical status: completed.**

The pinned native OpenSSL 3.5.9 build completed three fresh loopback TLS 1.3 handshakes for each candidate configuration:

| Case | Configuration | Result |
| --- | --- | --- |
| S0 | X25519 with ECDSA | passed, 3/3 |
| S2 | X25519MLKEM768 with ECDSA | passed, 3/3 |
| S3 | X25519MLKEM768 with ML-DSA-65 | passed, 3/3 |
| S4 | MLKEM768 with ML-DSA-65 | passed, 3/3 |

The source result table is [FEASIBILITY_RESULTS.md](phase-1/FEASIBILITY_RESULTS.md). Sanitized client-side evidence is retained in `evidence/feasibility/`.

S4 is an OpenSSL implementation-supported pure-PQ configuration. It must not be described as a hybrid mechanism defined by RFC 10024, which defines hybrid TLS groups.

## Phase 2 — Pilot

**Preparation status: protocol, README, C harness, configuration, and metadata template committed. Instrumentation smoke validation passed; pilot data collection is authorized and ready.**

The preparation and measurement plan are described in [PILOT_PROTOCOL.md](phase-2/PILOT_PROTOCOL.md) and [README.md](phase-2/README.md). The C client/server harness obtains handshake bytes and packet counts from the client's Linux per-socket `TCP_INFO` counters. Those values were validated against a loopback pcap for all four candidate configurations. Server/client receive counters are not reconciled because the server counter includes the TCP SYN sequence-space byte. Client/server CPU affinity is set to non-sibling P-cores CPU 0 and CPU 2. The pilot runner provides `--prepare-only` and `--smoke-test` modes; the smoke test creates no pilot data.

The initial S0 smoke handshake found a one-byte client/server receive-counter difference (266 client bytes sent versus 267 server bytes received). Pcap showed 266 TCP payload bytes; Linux counts the SYN sequence-space byte in the server receive counter. The client-side method then passed pcap validation for S0/S2/S3/S4. Smoke values are not pilot results and were not saved as a benchmark dataset. Run the authorized 10-warmup/30-measured pilot per case; do not begin Phase 3 until it is complete and reviewed.
