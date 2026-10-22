# PQC TLS Migration Study

This repository supports an empirical study of how a classical TLS 1.3 deployment can migrate toward post-quantum cryptography (PQC). The study is limited to a reproducible TLS 1.3 and OpenSSL case study; it does not claim results for all software systems.

## Research focus

The study compares cryptographic configurations separately from migration paths.

- **Configuration-level effects:** performance, resource use, communication overhead, and interoperability.
- **Migration-path effects:** configuration changes, compatibility outcomes, and case-specific migration effort.

The primary implementation stack is native OpenSSL 3.5.9 built from the
version-pinned source commit recorded in the environment manifest. OQS/liboqs,
if used, remains a separately documented auxiliary comparison and is not mixed
with primary results.

## Current scope

| Item | Decision |
| --- | --- |
| Protocol | TLS 1.3 |
| Primary stack | Native OpenSSL 3.5.9, source commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb` |
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

Phase 0 and Phase 1 feasibility work, the diagnostic pilots, and the final
controlled five-batch Ubuntu loopback campaign have been completed on the
primary platform. The final campaign contains 600 measured fresh handshakes
(150 per configuration), 200 retained warm-ups, batch metadata, and immutable
raw-artifact checksums. Its analysis is documented in
`docs/phase-3/FINAL_UBUNTU_ANALYSIS.md`.

The next empirical work is separately planned profile-compatibility testing,
controlled network sensitivity, and a limited Windows replication on the same
Intel hardware. These are not yet results and will not be retroactively mixed
with the primary campaign.

See [the phase status](docs/PHASE_STATUS.md), [the experimental protocol](docs/EXPERIMENTAL_PROTOCOL.md), and [the decision log](docs/DECISIONS.md).
