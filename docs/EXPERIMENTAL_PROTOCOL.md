# Experimental Protocol v1

## Objective

Measure how classical, hybrid, and post-quantum TLS 1.3/OpenSSL configurations affect computational performance, resource consumption, communication overhead, and interoperability; separately document the effort and compatibility implications of alternative migration paths.

## Research questions

- **RQ1:** How do classical, hybrid, and post-quantum TLS 1.3/OpenSSL configurations affect computational performance, resource consumption, communication overhead, and interoperability?
- **RQ2:** How do alternative migration paths from a classical TLS deployment to PQC differ in migration effort, configuration changes, and compatibility outcomes?
- **RQ3:** To what extent do controlled network conditions amplify the end-to-end effects of PQC and hybrid communication overhead?
- **RQ4:** To what extent are observed configuration-level effects consistent across Ubuntu and Windows on the same hardware, and across a secondary hardware platform?

## Phase 0: environment preparation and registration

Before generating certificates or measuring anything, record the OS release, kernel, CPU model, RAM, compiler, OpenSSL commit/version, build flags, CPU governor or power mode, and Git commit hash of this repository.

## Phase 1: feasibility validation

For every candidate configuration, record:

- TLS 1.3 handshake success or failure;
- negotiated TLS group;
- certificate and signature type;
- exact client/server command or configuration;
- relevant OpenSSL output and error log.

Only configurations with a reproducible successful handshake enter the benchmark matrix. A failure is retained as a compatibility finding, not silently discarded.

## Candidate configuration matrix

| ID | Key establishment | Authentication | Role | Feasibility status |
| --- | --- | --- | --- | --- |
| S0 | X25519 | ECDSA | Classical baseline | Pending |
| S2 | X25519MLKEM768 | ECDSA | Hybrid key establishment | Pending |
| S3 | X25519MLKEM768 | ML-DSA-65 | Hybrid key establishment with PQ authentication | Pending |
| S4 | ML-KEM-768, if TLS/OpenSSL supports it | ML-DSA-65 | PQ candidate | Pending |

## Phase 2: pilot

For every feasible configuration:

- execute 10 warm-up runs;
- collect 30 pilot observations;
- record handshake latency, CPU time or utilization, peak RSS, handshake bytes, packet count, and success/failure;
- inspect variance, logging correctness, and tool overhead before choosing the final repetition count.

## Phase 3: primary benchmark

- Use at least 50 repetitions per configuration and network condition; increase only if pilot variance justifies it.
- Randomize execution order across configurations.
- Record median, P50, P95, P99, a dispersion measure, and confidence intervals.
- Keep payload, TLS version, cipher suite, certificate chain, OpenSSL version, compiler, build flags, client concurrency, topology, warm-up policy, and measurement method fixed unless the experiment explicitly varies them.

## Phase 4: network sensitivity

Use a controlled native-Linux topology and `tc/netem`. Start with 0% loss and RTT values of 1 ms, 10 ms, 50 ms, and 100 ms. Add 0.1% and 1% loss only after the pilot confirms that the measurement harness is stable. Add bandwidth shaping only if pilot evidence shows it is relevant.

## Phase 5: validation

- Re-run a selected subset of successful primary experiments on Windows 11 using the same Intel Core i5-12450H.
- Re-run a selected subset on Ubuntu using the AMD A10-5800B.
- Treat these as validation analyses, not as a full duplicate of the primary matrix.

## Migration effort recording

For each transition, record raw descriptors rather than a synthetic score: files changed, configuration entries changed, dependencies or build changes, migration steps, test changes, failure/recovery events, and documented elapsed migration time. The measure is case-specific and must not be generalized as an industry-wide migration-effort index.
