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

**Preparation status: protocol, README, C harness, configuration, and metadata template prepared. Pilot data collection has not started.**

The preparation and measurement plan are described in [PILOT_PROTOCOL.md](phase-2/PILOT_PROTOCOL.md) and [README.md](phase-2/README.md). The C client/server harness obtains handshake bytes and packet counts from Linux per-socket `TCP_INFO` counters and validates client/server byte counts before accepting successful observations. Client/server CPU affinity is set to non-sibling P-cores CPU 0 and CPU 2. The pilot runner provides `--prepare-only` and `--smoke-test` modes; the smoke test creates no pilot data.

The pilot has been explicitly authorized. Do not begin Phase 3 until the 30-run-per-case pilot is complete and reviewed.
