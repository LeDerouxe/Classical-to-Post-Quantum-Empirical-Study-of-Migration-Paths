# Post-Quantum TLS 1.3 Migration: A Controlled Native OpenSSL Study of Configurations, Compatibility, and Network Sensitivity

## 5 Methodology

### 5.1 Study design and analytical scope

This work is a controlled empirical case study of selected TLS 1.3
configurations in native OpenSSL. It treats configuration behavior and
migration-path behavior as distinct analytical objects. Fresh-handshake
latency, communication descriptors, resource descriptors, and
same-configuration handshake outcomes are attributed to a configuration.
Configuration changes and profile compatibility are instead recorded as
properties of a transition path. This distinction avoids treating the
history-dependent work of migration as an intrinsic cost of a single
handshake.

The primary study was performed on native Ubuntu 26.04.1 running on an Intel
Core i5-12450H. It used OpenSSL 3.5.9 built from source commit
`45e844fa2a14ec92d146bd8f5778ac130b6625fb`. The scope is intentionally narrow:
the evidence concerns this pinned TLS 1.3/OpenSSL implementation, the stated
hardware and local credentials, and the controlled procedures described below.
It is not intended to estimate universal PQC performance, browser
interoperability, public-PKI behavior, or production deployment outcomes.

### 5.2 TLS configurations

All cases forced TLS 1.3 and `TLS_AES_128_GCM_SHA256`. Session tickets and
session caches were disabled. Each observation used a fresh client process and
a fresh server process configured to accept one connection. The four evaluated
configurations are listed in Table 1.

| Case | Key-establishment group | Server authentication |
| --- | --- | --- |
| S0 | X25519 | ECDSA P-256 |
| S2 | X25519MLKEM768 | ECDSA P-256 |
| S3 | X25519MLKEM768 | ML-DSA-65 |
| S4 | MLKEM768 | ML-DSA-65 |

**Table 1.** Evaluated TLS 1.3 configurations.

`X25519MLKEM768` is the hybrid TLS 1.3 key-establishment group standardized
by RFC 10024 [@RFC10024]. In contrast, S4 is described only as an
implementation-supported MLKEM768/ML-DSA-65 configuration in the pinned
OpenSSL build; it is neither labelled nor interpreted as a standardized hybrid
group. Before data collection, every configuration completed three independent
feasibility handshakes. A handshake was accepted only if the observed TLS
version, cipher suite, negotiated group, and CertificateVerify signature scheme
matched the requested configuration.

### 5.3 Primary Ubuntu campaign

The primary campaign contained five batches. In each batch, every case had ten
recorded warm-up handshakes followed by thirty measured fresh handshakes. The
warm-ups were retained as execution records but excluded from statistical
inference. The 120 measured handshakes within each batch were randomized over
the four cases using a recorded deterministic batch seed. The completed
campaign consequently comprised 200 warm-ups and 600 measured handshakes, or
150 measured observations per case.

The client and server were pinned to CPUs 2 and 4, respectively, after
confirming that they were distinct, non-sibling performance cores. CPU 0 was
left available to the operating system. The system was connected to AC power;
the system and platform profiles, CPU governor, and energy-performance
preference were required to be `performance` at the start and end of each
batch. A 120-second idle interval separated completed batches. For every batch,
the workflow retained the raw CSV, metadata, source and configuration identity,
planned and realized order, environment snapshots, timestamps, and SHA-256
integrity information.

### 5.4 Measurements

The primary endpoint was the client-side TLS-handshake duration, defined as the
`CLOCK_MONOTONIC_RAW` interval immediately around `SSL_connect()`. TCP-connect
duration was recorded separately. Client and server CPU times were per-thread
`getrusage` user-plus-system deltas over their documented role boundaries, and
peak resident-set size (RSS) was the `ru_maxrss` value of each fresh process.

Communication descriptors were obtained at successful `SSL_connect()` from
client-side Linux per-socket `TCP_INFO` counters: transmitted plus received TCP
payload bytes and observed TCP segments. A separate packet-capture smoke check
validated those counters for all four cases. No application payload was sent,
and session tickets were disabled. Thus, the communication descriptors cover
the defined handshake boundary; they exclude close packets and network headers
and do not estimate external-network transfer time.

### 5.5 Statistical analysis

All protocol-defined measured observations and completed batches were retained,
including statistically unusual values. Latency is summarized with the median
and interquartile range (IQR); mean, standard deviation, coefficient of
variation, P95, and P99 are reported only as descriptive diagnostics. The main
95% percentile-bootstrap intervals use 20,000 resamples: batches are resampled
first, then observations within each selected batch. A fixed-batch sensitivity
analysis resamples observations while retaining the five observed batch
memberships.

Configuration contrasts are median(case) minus median(S0), with batch-aware
bootstrap intervals. With only five observed batches, these intervals describe
campaign uncertainty; they are not null-hypothesis tests. Communication and
resource fields are secondary descriptors. Neither a measured observation nor
a completed batch is excluded merely because it appears unusual.

### 5.6 Migration-path and compatibility evidence

Migration was documented with transition descriptors rather than a synthetic
complexity score. The direct transition is S0-to-S4; the staged transition is
S0-to-S2-to-S3-to-S4. For each transition, the record identifies changes to
the group, signature scheme, certificate and trust material, hostname,
harness/build requirements, validation procedure, and same-configuration
handshake evidence. It does not estimate human labor, PKI operations,
mixed-version interoperability, rollback behavior, or production deployment
risk.

A separate compatibility follow-up evaluated four profiles: legacy (L),
hybrid-key-establishment transition (H), dual-capable transition (D), and
strict PQ (Q). Before collection, a single native-OpenSSL server context with a
certificate-selection callback had to demonstrate ECDSA P-256 selection for an
L client and ML-DSA-65 selection for a D client. The gate used fresh local test
credentials, TLS 1.3, and the same pinned OpenSSL build.

After the gate passed, every ordered client/server profile pair was attempted
three times in recorded randomized order, giving 48 fresh attempts. The matrix
retained negotiated parameters, certificate selection, verification outcomes,
and sanitized failure information; it did not collect performance data. A TCP
connection alone was insufficient: a success required TLS completion as well as
certificate-chain and hostname validation.

### 5.7 Windows direction-validation follow-up

A separate native Windows 11 campaign used the same physical Intel Core
i5-12450H, the same OpenSSL source commit, TLS version, cipher suite, four
configurations, fresh-process design, and five-batch structure. The Windows
client measured the `SSL_connect()` interval with QueryPerformanceCounter.
Before collection, the workflow required AC power, the explicitly selected
`High performance` scheme, valid local credentials, the pinned OpenSSL
identity, and two active, non-sibling performance-class cores. It recorded
process affinity, configuration validation, and environment snapshots before
and after every batch.

The Windows analysis used the same median, IQR, and 20,000-resample
batch-aware percentile-bootstrap approach as the primary Ubuntu analysis. Its
role was qualitative: it tested whether the direction of each within-Windows
S0 contrast agreed with the Ubuntu direction. The Windows and Ubuntu datasets
were not pooled, and the design does not estimate a Windows-minus-Ubuntu
absolute-latency difference or an operating-system effect. Linux-specific
`TCP_INFO` and `getrusage` descriptors were not replicated on Windows.

### 5.8 Controlled network-sensitivity follow-up

A separate native-Ubuntu follow-up evaluated the same four configurations at
five prespecified added-RTT conditions: 0, 1, 10, 50, and 100 ms. Two dedicated
Linux network namespaces were connected by one veth pair. Symmetric `tc netem`
egress delay was applied at both endpoints, such that the two one-way delays
summed to the stated RTT. The 0-ms condition is a topology control and not a
duplicate of the primary loopback experiment.

Each condition had five randomized batches. A batch contained ten retained
warm-ups and thirty measured fresh handshakes per case, giving 150 measured
observations per case and condition. All 25 condition-batches were randomized.
Before and after each batch, the workflow verified the namespace topology,
qdisc state, local-credential validity, OpenSSL identity, AC power, and the
same affinity and performance guards used in the primary campaign.

The network analysis retained all 3,000 measured observations and used the
same condition-specific, batch-aware bootstrap design as the primary analysis.
RTT conditions were not pooled. The setup did not emulate packet loss,
bandwidth limits, jitter, congestion, reordering, browsers, public PKI, or an
Internet path.
