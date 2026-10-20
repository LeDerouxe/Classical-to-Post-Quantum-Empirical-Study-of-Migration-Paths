# Research Decision Log

This log records decisions that constrain the study design. A later change must add a dated entry explaining the reason and its effect on reproducibility.

## D-001 Study boundary

- **Status:** accepted
- **Decision:** Study a TLS 1.3 and OpenSSL case study rather than claiming behavior for all software systems.
- **Rationale:** The boundary is concrete, operationally realistic, and experimentally controllable.

## D-002 Analytical unit

- **Status:** accepted
- **Decision:** Treat cryptographic configurations and migration paths as distinct analytical units.
- **Rationale:** A single handshake has a configuration, not a history of the path used to reach it. System and communication metrics will be attributed to configurations; migration effort and transition compatibility will be attributed to paths.

## D-003 Primary cryptographic stack

- **Status:** accepted
- **Decision:** Use native OpenSSL 3.5.9, source commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb`, for primary experiments.
- **Rationale:** A fixed native stack reduces implementation confounding. OQS/liboqs may be used only in a separately reported auxiliary comparison.

## D-004 Candidate configurations

- **Status:** accepted; feasibility confirmed on the pinned primary stack
- **Decision:** Use X25519 + ECDSA, X25519MLKEM768 + ECDSA, X25519MLKEM768 + ML-DSA-65, and ML-KEM-768 + ML-DSA-65 in the primary configuration matrix.
- **Rationale:** These candidates cover classical, hybrid, and post-quantum transitions while maintaining a focused scope.

## D-005 Experimental platforms

- **Status:** accepted
- **Decision:** Use Ubuntu 26.04.1 LTS on the Intel Core i5-12450H as the primary native environment; use Windows 11 on the same hardware for cross-OS validation; use Ubuntu on AMD A10-5800B for secondary hardware-sensitivity validation.
- **Rationale:** The same-CPU OS comparison controls a major confounder. The AMD system is a secondary validation platform, not a second primary experiment matrix.

## D-006 Network experiments

- **Status:** accepted
- **Decision:** Run controlled network-sensitivity experiments on native Linux with `tc/netem`, separately from the Windows-versus-Ubuntu comparison.
- **Rationale:** `netem` is a Linux control mechanism; its results should not be interpreted as a direct network-stack comparison with Windows.

## D-007 Citation quality

- **Status:** accepted
- **Decision:** Cite only references verified against primary standards, publisher records, or the publisher-hosted full text. Record supporting sections/pages in a citation evidence matrix before final manuscript use.
- **Rationale:** Citation precision is a non-negotiable requirement for peer review.
