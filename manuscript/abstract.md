# Abstract

Post-quantum migration in TLS 1.3 changes more than one cryptographic
primitive: it can change key establishment, authentication material,
negotiation policy, and peer compatibility. This paper presents a controlled,
reproducible case study of four native OpenSSL 3.5.9 configurations: an
X25519/ECDSA P-256 baseline (S0), X25519MLKEM768/ECDSA P-256 (S2),
X25519MLKEM768/ML-DSA-65 (S3), and an implementation-supported
MLKEM768/ML-DSA-65 configuration (S4). The primary Ubuntu 26.04.1 experiment
on an Intel Core i5-12450H retained 600 fresh TLS 1.3 handshakes across five
randomized batches. Median `SSL_connect()` duration was 0.834 ms for S0,
0.989 ms for S2, 1.436 ms for S3, and 1.312 ms for S4; every non-classical
case had a positive median contrast relative to S0 in every batch. A separate
4-by-4 migration-profile matrix recorded 36 successful and 12 no-common-group
outcomes in 48 local native-OpenSSL attempts; the defined dual-capable profile
bridged the other evaluated profiles. A separate Windows campaign on the same
hardware reproduced the direction of all within-platform contrasts without
pooling timings. Finally, a 3,000-observation namespace/veth/netem follow-up
showed that, under fixed added RTT, the S3 and S4 contrasts were close to one
additional RTT at 10, 50, and 100 ms, whereas S2 remained close to S0. These
findings are bounded to the pinned implementation, hardware, local
credentials, and controlled transport conditions. They do not establish
Internet-scale interoperability, browser behavior, production performance, or
causal network mechanisms. The accompanying raw artifacts, metadata, and
analysis scripts make each reported result auditable.
