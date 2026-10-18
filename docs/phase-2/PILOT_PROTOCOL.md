# Phase 2 Pilot Protocol

## Scope and gate

This is a native Ubuntu loopback pilot for S0, S2, S3, and S4. It collects 10 warm-up handshakes and 30 measured handshakes per case. The 120 measured handshakes are shuffled together using the recorded seed. This pilot assesses harness behavior and measurement variance; it is not a performance conclusion.

The Phase 2 pilot was explicitly authorized after Phase 0/1 acceptance. Do not start Phase 3 without review of the completed pilot and explicit approval.

## Fixed controls

- Server and client run on `127.0.0.1` on the same native Ubuntu 26.04.1 host.
- TLS is forced to 1.3 and cipher suite `TLS_AES_128_GCM_SHA256`.
- Every observation uses a new client process and a fresh one-accept server process. Both disable tickets and session caches; no session object is reused.
- Each case sets its requested TLS group, signature scheme, and local self-signed server certificate explicitly. The client validates the certificate and hostname.
- One C harness source implements client and server modes and links against the pinned local OpenSSL 3.5.9 shared libraries. The Python runner only schedules processes, randomizes cases, records metadata, and writes CSV; Python/process timing is not used as the latency metric.
- The server is started and signals readiness before the client is launched. C timing starts at `connect()` for `tcp_connect_ns` and immediately before `SSL_connect()` for `tls_handshake_ns`; harness compilation, process startup, OpenSSL context setup, and server startup are excluded from those intervals.
- Linux CPU topology reports four 4.4 GHz maximum-frequency P-core sibling pairs: CPUs 0/1, 2/3, 4/5, and 6/7. Four 3.3 GHz maximum-frequency CPUs 8–11 are E-cores. The pilot pins the client to CPU 0 and server to CPU 2, distinct non-sibling P-cores. No governor, EPP, or power-mode change is made.
- No `tc/netem`, packet loss, bandwidth shaping, Windows, AMD, or external network is used.

## Candidate matrix

| Case | Requested group | Requested signature scheme | Certificate |
|---|---|---|---|
| S0 | `x25519` | `ecdsa_secp256r1_sha256` | ECDSA P-256 |
| S2 | `X25519MLKEM768` | `ecdsa_secp256r1_sha256` | ECDSA P-256 |
| S3 | `X25519MLKEM768` | `mldsa65` | ML-DSA-65 |
| S4 | `MLKEM768` | `mldsa65` | ML-DSA-65 |

Names use the spellings returned by pinned OpenSSL 3.5.9.

## Measurement definitions

- `tcp_connect_ns`: `CLOCK_MONOTONIC_RAW` duration around the client TCP `connect()` call.
- `tls_handshake_ns`: `CLOCK_MONOTONIC_RAW` duration around client `SSL_connect()`. This is the primary pilot latency field.
- Client and server CPU nanoseconds: per-thread `getrusage(RUSAGE_THREAD)` user/system CPU deltas. Client interval covers TCP connect plus TLS handshake; server interval covers `SSL_accept()`.
- Peak RSS: per-process `getrusage(RUSAGE_SELF).ru_maxrss`, in KiB. Each observation has a fresh client and server process.
- `handshake_bytes`: client-side `TCP_INFO.tcpi_bytes_sent + tcpi_bytes_received`, sampled immediately after successful `SSL_connect()`. These counters report TCP payload octets, excluding link/IP/TCP headers. No application data is sent and tickets are disabled, so successful-flow payload at this boundary is TLS handshake data.
- `packet_count`: client-side `TCP_INFO.tcpi_segs_out + tcpi_segs_in` at the same boundary. This is the kernel's count of TCP segments observed on that socket from connection setup through completed `SSL_connect()`, including SYN/ACK/control segments and any retransmissions before that boundary. It excludes connection-close packets, which occur after the sample. It is not an approximate proxy. Linux exposes these per-socket counters as `tcpi_segs_out` and `tcpi_segs_in`.

The harness refuses to emit a successful observation if `TCP_INFO` is unavailable or if the negotiated TLS version, cipher, group, or signature type does not match the requested case. The server-side counters are retained for diagnostics, but they are not combined with or reconciled against client-side counters.

### Instrumentation smoke validation (2026-10-18)

On this host, `tcpdump` capture on `lo` was enabled for smoke validation only. One fresh handshake per candidate was captured and compared with the client-side `TCP_INFO` counters at the harness's `SSL_connect()` completion boundary. For S0/S2/S3/S4 respectively, pcap payload totals matched `handshake_bytes` (967/3231/11595/11531), and counts of TCP segments through the final handshake ACK matched `packet_count` (8/8/12/12). The captures also showed three additional TCP close packets after the `SSL_connect()` sample; these are not included. No packet capture runs during pilot measurements, avoiding capture-path overhead in the measured runs.

The first S0 trial showed a one-byte difference between the client and server receive counters: the client reported 266 bytes sent, while the server reported 267 bytes received. Pcap confirmed 266 actual TCP payload bytes in that direction; Linux's server-side `TCP_INFO` receive counter includes the SYN sequence-space byte on this loopback flow. Therefore the protocol uses the validated client-side counters only. The four-case smoke test generated no pilot CSV and no benchmark data.

## Execution and immutable outputs

1. Build `scripts/pilot/tls_pilot.c` with `scripts/pilot/run_pilot.py` against the pinned OpenSSL headers and shared libraries.
2. Run 10 warm-ups per case, then run all 120 measured observations in one shuffled sequence generated from `random_seed` in `configs/pilot/pilot.json`.
3. Store all 160 rows (including warm-ups and explicit flags) in one new, read-only CSV under `data/raw/pilot/`. A unique run ID and exclusive file creation prevent overwrite. Store matching run metadata and CSV SHA-256 under `data/metadata/pilot/`.
4. Keep credentials, build outputs, and operational logs ignored. The raw pilot CSV is expected to be a small text file and may be committed only after checking row counts, schema, successful statuses, and checksum. Never edit a completed raw CSV; corrections require a new run and file.

## Stop condition

After 30 measured observations per configuration, report the Git commit, case/run status, raw-data path and checksum, and preliminary variance/measurement-quality observations. Make no performance claim and do not begin Phase 3.
