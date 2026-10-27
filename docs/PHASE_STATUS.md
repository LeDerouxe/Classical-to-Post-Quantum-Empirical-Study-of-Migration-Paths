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

## Phase 2 — Original diagnostic pilot

**Pilot status: completed and retained as a historical diagnostic run; it is not
used for primary performance conclusions.**

The preparation and measurement plan are described in [PILOT_PROTOCOL.md](phase-2/PILOT_PROTOCOL.md) and [README.md](phase-2/README.md). This original run used client/server affinity on non-sibling P-cores CPU 0 and CPU 2, with the then-current power policy unchanged. The C client/server harness obtains handshake bytes and packet counts from the client's Linux per-socket `TCP_INFO` counters. Those values were validated against a loopback pcap for all four candidate configurations. Server/client receive counters are not reconciled because the server counter includes the TCP SYN sequence-space byte. The pilot runner provides `--prepare-only` and `--smoke-test` modes; the smoke test creates no pilot data.

The initial S0 smoke handshake found a one-byte client/server receive-counter difference (266 client bytes sent versus 267 server bytes received). Pcap showed 266 TCP payload bytes; Linux counts the SYN sequence-space byte in the server receive counter. The client-side method then passed pcap validation for S0/S2/S3/S4. The pilot was collected at commit `442b65ffd0adfcdd0da2a2eec5bc0993fe53800a`; its 160 rows, metadata, checksum, and preliminary variance checks are recorded in [PILOT_REPORT.md](phase-2/PILOT_REPORT.md).

## Phase 2B — Stabilization pilot

**30 measured runs per case completed and accepted as a diagnostic stabilization pilot.** Phase 2B used client/server CPUs 2/4 (non-sibling P-cores, leaving CPU 0 available) and the user-approved `performance` profile, governor, and EPP policy. Its environment snapshots, CSV, metadata, and checksum are documented in [PHASE-2B-REPORT.md](phase-2/PHASE-2B-REPORT.md). The Phase 2 and Phase 2B raw CSVs, metadata, and reports are preserved unchanged. No comparative performance result is reported here.

## Final multi-batch measurement — primary Ubuntu loopback campaign

**Technical status: completed.** One authorized, non-resumed campaign completed
five batches using the pinned native OpenSSL 3.5.9 build. It contains 800 rows:
200 retained warm-ups and 600 measured fresh handshakes (150 per S0, S2, S3,
and S4). All handshakes succeeded and all configuration validations passed.

The campaign used client/server CPUs 2/4, with CPU 0 left to the operating
system. AC status, performance profiles, governor, and EPP guards passed at
the start and end of every batch. The immutable raw CSVs, metadata, and
checksums are recorded in
[FINAL-CAMPAIGN-INTEGRITY-20261020.md](phase-2/FINAL-CAMPAIGN-INTEGRITY-20261020.md).
The reproducible primary analysis is recorded in
[FINAL_UBUNTU_ANALYSIS.md](phase-3/FINAL_UBUNTU_ANALYSIS.md).

## Planned follow-up studies

The approved profile-compatibility design is recorded in
[PROFILE_COMPATIBILITY_PROTOCOL.md](phase-4/PROFILE_COMPATIBILITY_PROTOCOL.md).
It includes a mandatory native-OpenSSL dual-certificate selection gate before
its 4-by-4 profile matrix can run. Collection has not started.

Controlled network sensitivity and a limited Windows replication remain
planned distinct studies. They have not started and must not be described as
completed results.
