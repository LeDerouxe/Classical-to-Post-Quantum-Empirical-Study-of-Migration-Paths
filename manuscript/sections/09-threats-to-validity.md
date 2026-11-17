# 9 Threats to Validity and Scope

## 9.1 Construct validity

The primary latency endpoint is the client-side monotonic interval around
`SSL_connect()`. It captures the selected fresh TLS handshake boundary, not
DNS resolution, application data transfer, session resumption, connection
teardown, user-visible page load, or end-to-end service latency. TCP_INFO
bytes and segments describe the client-side handshake boundary; they are not
wire-header accounting or a measure of application traffic. Per-process CPU
time and peak RSS are run-level descriptors, not total-system or
production-server resource measurements.

The compatibility matrix measures completion and local certificate and
hostname verification for defined native-OpenSSL profiles. It does not measure
browser behavior, public-PKI validation, external trust stores, version
negotiation outside the matrix, or deployment policy. S4 is an
implementation-supported MLKEM768/ML-DSA-65 configuration in the pinned
build; it is not represented as an RFC 10024 hybrid group.

## 9.2 Internal validity

The performance campaigns used fresh client and server processes, fixed TLS
version and cipher suite, recorded randomized orders, explicit affinity, and
before/after guards for AC power and performance policy. These controls reduce
but cannot eliminate run-to-run variation. Temperature and frequency
snapshots do not constitute continuous telemetry, and ordinary operating-system
activity was not eliminated.

The study retained every protocol-defined measured observation and completed
batch, including unusual values. The bootstrap intervals resample the five
observed batches and therefore describe uncertainty for this campaign rather
than provide a null-hypothesis test or compensate for unmeasured confounders.
No independent repeat of the entire final campaign was collected.

## 9.3 External validity

The primary evidence is one native OpenSSL 3.5.9 source build on one Intel
Core i5-12450H system running Ubuntu 26.04.1. It cannot establish behavior for
other processors, operating systems, OpenSSL versions, TLS libraries,
cryptographic providers, algorithm parameter sets, or deployment sizes. The
separate Windows campaign is a directional validation on the same physical
hardware, not a second population from which to estimate a platform effect.

The network campaign uses two local namespaces connected by one veth pair and
fixed symmetric `tc netem` delay. It has no induced loss, jitter, bandwidth
cap, congestion, reordering, competing traffic, NAT, proxy, middlebox, public
Internet route, or browser stack. Its results should not be read as a general
network model. The locally generated credentials and controlled hostnames also
do not model public CA issuance, certificate-transparency workflows,
certificate-management systems, or real trust-store diversity.

## 9.4 Reproducibility and evidence integrity

The scope is strengthened by version pinning, raw CSVs, per-batch metadata,
environment snapshots, checksums, retained warm-ups, recorded execution
orders, and analysis scripts. These artifacts support reproduction and audit
of the reported case study, but they do not by themselves guarantee bitwise
or timing-identical results on a different machine or at a different time.
The analysis and manuscript result audit are designed to detect discrepancies
between raw artifacts and reported values; they are not substitutes for an
independent replication.
