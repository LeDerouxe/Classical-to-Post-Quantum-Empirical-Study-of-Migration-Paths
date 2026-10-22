# 1 Introduction

Transport Layer Security (TLS) 1.3 establishes a secure channel through a
handshake that negotiates cryptographic parameters, authenticates peers, and
establishes shared keying material [@TLS9846].  The public-key choices made in
that handshake are therefore a concrete migration surface for post-quantum
cryptography (PQC).  NIST has standardized ML-KEM for key encapsulation
[@NISTFIPS203] and ML-DSA for digital signatures [@NISTFIPS204].  In parallel,
RFC 10024 standardizes the `X25519MLKEM768` hybrid key-agreement group for TLS
1.3 [@RFC10024].

These developments make a TLS transition more than a substitution of one
primitive for another.  Key establishment, authentication material,
negotiation policy, certificates, peer capabilities, and the implementation
stack jointly determine the behavior of a deployed configuration.  A useful
empirical study must consequently distinguish configuration-level effects from
the operational path by which a deployment moves between configurations.

Prior studies have established the importance of measuring post-quantum TLS in
context.  Sikeridis *et al.* evaluate post-quantum authentication and its
connection-establishment and throughput implications under realistic network
conditions [@Sikeridis2020].  Sosnowski *et al.* jointly examine
post-quantum key-agreement and signature choices, including handshake latency,
transmitted data, and constrained-network conditions [@Sosnowski2023].
Montenegro *et al.* provide an OpenSSL/OQS-based framework for evaluating
classical, hybrid, and post-quantum TLS configurations across controlled and
scenario-based conditions [@Montenegro2026].  Their different implementation
stacks and designs also make direct comparison of absolute measurements
inappropriate.

This paper presents a reproducible controlled case study of four TLS 1.3
configurations in native OpenSSL 3.5.9: a classical X25519/ECDSA P-256
baseline; `X25519MLKEM768` with ECDSA P-256; `X25519MLKEM768` with ML-DSA-65;
and an implementation-supported MLKEM768/ML-DSA-65 configuration.  The primary
study uses native Ubuntu 26.04.1 on an Intel Core i5-12450H.  It reports fresh
handshake latency, resource descriptors, communication descriptors, negotiated
parameters, and within-configuration handshake outcomes.  It does not claim
universal performance, Internet-scale interoperability, or production
deployment behavior.

The study makes three contributions.  First, it uses a version-pinned native
OpenSSL build and an immutable five-batch campaign with randomized measured
handshakes, retained warm-ups, environment guards, and raw-artifact checksums.
Second, it estimates configuration-level latency contrasts with a batch-aware
bootstrap and a fixed-batch sensitivity analysis, without deleting measured
observations.  Third, it records migration paths separately as auditable
configuration-change and compatibility descriptors rather than treating a
history-dependent transition as an intrinsic cost of one handshake.

The paper addresses the following research questions:

- **RQ1:** Within the controlled native Ubuntu/OpenSSL environment, how do the
  four selected TLS 1.3 configurations differ in fresh-handshake latency,
  resource descriptors, communication descriptors, and same-configuration
  handshake outcomes?
- **RQ2:** What configuration changes and compatibility evidence characterize
  the direct and staged migration paths from the classical baseline toward the
  evaluated post-quantum configurations?
- **RQ3:** How do controlled network conditions affect the configuration
  contrasts observed in this case study?
- **RQ4:** To what extent do the directions of the primary contrasts replicate
  in a separately reported cross-operating-system validation on the same
  hardware?

RQ1 is answered by the completed primary campaign.  RQ2--RQ4 are reported only
after their separately versioned compatibility, network-sensitivity, and
cross-operating-system studies have been completed; until then, they define
the study plan rather than empirical findings.
