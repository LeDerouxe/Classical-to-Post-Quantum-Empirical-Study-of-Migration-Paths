# 5 Methodology

## 5.1 Study design and scope

This study is a controlled empirical case study of TLS 1.3 configurations in
native OpenSSL. Its analytical unit is deliberately split in two. Runtime,
resource, communication, and same-configuration handshake outcomes are
attributed to cryptographic configurations. Migration effort and transition
compatibility are documented separately as path-level descriptors. This
separation avoids attributing a history-dependent migration path to an
individual handshake.

The primary experiment uses native Ubuntu 26.04.1 on an Intel Core i5-12450H.
OpenSSL 3.5.9 was built from source commit
`45e844fa2a14ec92d146bd8f5778ac130b6625fb`. The study is bounded to this
TLS 1.3/OpenSSL case study; it does not claim universal results for PQC
migration, other software stacks, or production deployments.

## 5.2 Configuration matrix

All cases force TLS 1.3 and `TLS_AES_128_GCM_SHA256`. Tickets and session
caches are disabled, and every observation uses a fresh client process and a
fresh one-accept server process. The configurations are shown below.

| Case | Key-establishment group | Authentication |
| --- | --- | --- |
| S0 | X25519 | ECDSA P-256 |
| S2 | X25519MLKEM768 | ECDSA P-256 |
| S3 | X25519MLKEM768 | ML-DSA-65 |
| S4 | MLKEM768 | ML-DSA-65 |

S4 is treated as an implementation-supported pure-PQ configuration in the
pinned OpenSSL build. It is not described as a standardized hybrid group.

Before measurement, each configuration completed three independent feasibility
handshakes. The harness rejected successful output unless the negotiated TLS
version, cipher suite, group, and signature scheme matched the requested case.

## 5.3 Measurement procedure

The final campaign comprised five batches. Each batch contained ten warm-up
handshakes and thirty measured handshakes for each case. The 40 warm-ups per
batch were recorded but excluded from statistical inference. The 120 measured
observations per batch were fully randomized across the four cases using a
recorded deterministic batch seed. The campaign therefore produced 600
measured observations, or 150 per case.

The client was pinned to CPU 2 and the server to CPU 4 after verification that
they were distinct non-sibling P-cores; CPU 0 was left available to the
operating system. The system was connected to AC power. System and platform
profiles, CPU governor, and energy-performance preference were required to be
`performance` before and after every batch. The workflow recorded immutable
CSV and metadata files per batch, with source/configuration identities,
environment snapshots, timestamps, planned and realized order, and checksums.
A 120-second idle interval separated completed batches.

## 5.4 Measurements

The primary endpoint was client-side TLS handshake duration: the
`CLOCK_MONOTONIC_RAW` interval immediately around `SSL_connect()`. TCP connect
duration was recorded separately. Client and server CPU times are per-thread
`getrusage` user-plus-system deltas over their documented role boundaries.
Peak RSS is the per-process `ru_maxrss` value for each fresh process.

Communication overhead was measured from client-side Linux per-socket
`TCP_INFO` counters at completed `SSL_connect()`: transmitted plus received
TCP payload bytes and observed TCP segments. Packet capture validated these
counters for all four cases during a separate instrumentation smoke check.
No application payload was sent, and tickets were disabled. The counters thus
describe the handshake boundary and exclude close packets and network headers.

## 5.5 Analysis

All successful measured observations were retained, including statistically
unusual values. Latency is summarized with median and IQR; mean, standard
deviation, CV, P95, and P99 are descriptive diagnostics. The primary 95%
percentile bootstrap intervals use 20,000 resamples that first resample the
five batches and then observations within selected batches. A sensitivity
analysis resamples observations while retaining the five observed batch
memberships. With five batches, intervals are reported as uncertainty
descriptions rather than as null-hypothesis tests.

Configuration contrasts are reported as median(case) minus median(S0), with
batch-aware bootstrap intervals. Communication and resource fields are
reported as secondary descriptors. The analysis never discards a completed
batch or an observation solely because it is an outlier.

## 5.6 Migration-path descriptors

The migration analysis records raw transition descriptors instead of a
synthetic complexity index. The direct path is S0 to S4. The staged path is
S0 to S2 to S3 to S4. For each transition, the study records changes to group,
signature, certificate/trust material, hostname, harness/build requirements,
validation procedure, and same-configuration compatibility evidence. Human
labor time, PKI operations, mixed-version interoperability, rollback, and
production deployment effects were not measured and are reported as such.
