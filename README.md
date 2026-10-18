# PQC TLS Migration Study

This repository supports an empirical study of how a classical TLS 1.3 deployment can migrate toward post-quantum cryptography (PQC). The study is limited to a reproducible TLS 1.3 and OpenSSL case study; it does not claim results for all software systems.

## Research focus

The study compares cryptographic configurations separately from migration paths.

- **Configuration-level effects:** performance, resource use, communication overhead, and interoperability.
- **Migration-path effects:** configuration changes, compatibility outcomes, and case-specific migration effort.

The primary implementation stack will use a version-pinned native OpenSSL 3.5.x release. OQS/liboqs, if used, will remain a separately documented auxiliary comparison and will not be mixed with primary results.

## Current scope

| Item | Decision |
| --- | --- |
| Protocol | TLS 1.3 |
| Primary stack | Native OpenSSL 3.5.x, exact patch version to be pinned during setup |
| Classical baseline | X25519 with ECDSA authentication |
| Hybrid candidate | X25519MLKEM768 with ECDSA authentication |
| PQ authentication candidate | ML-DSA-65 |
| Primary platform | Ubuntu 26.04.1 LTS on Intel Core i5-12450H |
| Cross-OS validation | Windows 11 on the same Intel hardware |
| Secondary validation | Ubuntu on AMD A10-5800B |

The final configuration matrix is conditional on successful TLS/OpenSSL feasibility validation. No candidate is treated as benchmark-ready before its negotiated group, certificate/signature type, and handshake behavior are verified.

## Repository layout

```text
docs/       Research protocol, decisions, and citation evidence
configs/    Versioned OpenSSL, benchmark, and network configurations
scripts/    Setup, feasibility, benchmark, and analysis automation
data/       Local experimental data; raw results are ignored by Git
```

## Working rules

1. Every meaningful file change is committed with a descriptive message.
2. Benchmark results are never committed without environment metadata and the Git commit hash that produced them.
3. Raw measurement data is immutable after collection; corrected or derived datasets are stored separately.
4. Private keys, certificates with personal data, build artifacts, and large raw captures are never committed.
5. Every reference used in the manuscript must be verified against its primary source or publisher record before it is cited.

## Next milestone

Phase 0 and Phase 1 feasibility work has been collected on the primary Ubuntu platform. Repository integration and the pinned OpenSSL reproducibility check are recorded in the environment manifest. Phase 2 pilot setup and its controlled C TLS harness are documented in `docs/phase-2/`; do not begin Phase 3 before the pilot is reviewed.

See [the phase status](docs/PHASE_STATUS.md), [the experimental protocol](docs/EXPERIMENTAL_PROTOCOL.md), and [the decision log](docs/DECISIONS.md).
