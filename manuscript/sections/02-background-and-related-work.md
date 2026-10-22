# 2 Background and Related Work

## 2.1 TLS 1.3 and post-quantum choices

TLS 1.3 separates the negotiation of public-key key establishment and
authentication from the record-protection cipher suite [@TLS9846].  This
separation is material to migration experiments: a change in the negotiated
key-establishment group and a change in certificate/signature material are
distinct interventions, even when both occur within the same handshake.

ML-KEM is standardized in FIPS 203 as a key-encapsulation mechanism with
ML-KEM-512, ML-KEM-768, and ML-KEM-1024 parameter sets [@NISTFIPS203].
ML-DSA is standardized in FIPS 204 for digital-signature generation and
verification [@NISTFIPS204].  For TLS 1.3, RFC 10024 specifies
`X25519MLKEM768` as a hybrid group that combines X25519 ECDHE and ML-KEM-768
[@RFC10024].  In contrast, the MLKEM768 case evaluated here is an
implementation-supported pure-PQ configuration of the pinned OpenSSL build;
it is not labelled a standardized hybrid group.

## 2.2 Empirical post-quantum TLS studies

Empirical work has measured several layers of the PQ-TLS problem.  Sikeridis
*et al.* focus on post-quantum authentication, evaluating signature candidates
and their effects on TLS 1.3 connection establishment and server throughput
under realistic network conditions [@Sikeridis2020].  This establishes that
authentication deserves separate system-level treatment, rather than being
reduced to a signature microbenchmark.

Sosnowski *et al.* evaluate both key-agreement and signature choices with
end-to-end and component-level measurements, and include emulated loss,
bandwidth, and delay [@Sosnowski2023].  Montenegro *et al.* subsequently
provide a framework for comparing classical, hybrid, and post-quantum TLS
configurations, including controlled-network and scenario-based evaluation
[@Montenegro2026].  These studies motivate measuring both compute-adjacent and
communication-facing descriptors, while also showing why raw latency values
cannot be transferred across implementations, hosts, certificates, or network
setups.

The present study complements this literature rather than attempting a
cross-paper performance ranking.  It uses a pinned native OpenSSL 3.5.9 build,
validates negotiated parameters per observation, separates hybrid
key-establishment changes from post-quantum authentication changes, and treats
migration paths as configuration and compatibility records.  Its primary
conclusions are deliberately limited to the controlled Ubuntu loopback case
study.
