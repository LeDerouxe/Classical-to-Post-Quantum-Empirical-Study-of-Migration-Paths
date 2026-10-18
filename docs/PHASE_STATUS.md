# Phase Status

## Phase 0 — Environment preparation and registration

**Technical status: completed, pending repository integration on Ubuntu.**

The primary native Ubuntu 26.04.1 environment, version-pinned OpenSSL 3.5.9 build, and algorithm inventory are recorded under `environment/ubuntu-26.04.1/`.

The initial collection occurred before the Ubuntu workspace was cloned from the research repository. After pulling this commit, the Ubuntu workspace must update the repository-registration section of the manifest with the repository URL, branch, and commit hash that reproduce the work.

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

## Next permitted action

No pilot or benchmark has been run. The next action is repository integration and a reproducibility check on Ubuntu; Phase 2 begins only after that check is committed and reviewed.
