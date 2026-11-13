# Controlled network-sensitivity protocol

## Purpose and boundary

This is Step 5 of the project roadmap and addresses RQ3. It evaluates whether
the within-platform configuration contrasts observed in the Ubuntu loopback
campaign retain their direction under controlled, deterministic added delay.
It is a separate campaign; it does not alter, replace, or pool with the
completed loopback or Windows datasets.

The study uses two dedicated Linux network namespaces linked only by a veth
pair. It does not alter a physical interface, use the public Internet, or
emulate a browser, public PKI, congestion, bandwidth limit, jitter, loss,
reordering, duplication, or corruption. Fixed delay is applied symmetrically
to veth egress in both namespaces using `tc netem`, so the configured one-way
delay sums to the stated RTT. The topology is removed only by the explicit
teardown command after evidence review.

## Fixed conditions

| Condition | Added RTT | Per-direction netem delay |
| --- | ---: | ---: |
| `rtt-000ms` | 0 ms | 0 ms |
| `rtt-001ms` | 1 ms | 500 microseconds |
| `rtt-010ms` | 10 ms | 5 ms |
| `rtt-050ms` | 50 ms | 25 ms |
| `rtt-100ms` | 100 ms | 50 ms |

The 0-ms veth condition is a topology control. It separates namespace/veth
effects from delay effects; it is not treated as a duplicate of the loopback
primary campaign. Loss and bandwidth shaping are excluded from this campaign.
They require separate protocol, sample-size, and interpretation decisions.

All conditions retain the pinned OpenSSL source, TLS 1.3, cipher suite, case
matrix, fresh-process design, local credentials, AC requirement, performance
power policy, P-core affinity (client CPU 2, server CPU 4), warm-up policy,
and batch-aware analysis principle used in the primary Ubuntu campaign.

## Gates and collection

1. A privileged setup script creates only `pqc-tls-client`, `pqc-tls-server`,
   and their veth endpoints. It refuses to overwrite pre-existing dedicated
   namespaces.
2. Preflight confirms the topology, exact addresses, MTU 1500, OpenSSL identity,
   current validity of the local credentials, CPU/power guards, and root qdisc
   snapshots. It creates evidence only.
3. Smoke performs one fresh handshake per case at `rtt-000ms`, checks the
   requested TLS negotiation and both endpoint TCP_INFO availability, and
   creates evidence only.
4. One main campaign collects five batches per condition. Each batch contains
   ten retained warm-ups and thirty measured observations per case, randomized
   within warm-up and measured blocks. The 25 condition-batches are also
   randomly ordered with a recorded seed. Thus each condition has 800 rows
   and 600 measured observations; the full campaign has 4,000 rows and 3,000
   measured observations.

Every batch records environment and `tc -s qdisc` snapshots before and after
collection. A failed handshake, missing guard, changed qdisc, interruption, or
partial batch is retained and stops the campaign. A completed batch is never
overwritten, resumed, or merged with another campaign.

## Analysis and interpretation

For each condition, summarize `SSL_connect()` duration, TCP connect duration,
client-side TCP_INFO bytes/segments, and handshake outcomes by case and batch.
The prespecified contrast is median(case) minus median(S0), with a
condition-specific batch-aware bootstrap interval. Analyze delay conditions
separately and report their batch-level direction; do not pool conditions or
fit an unplanned global latency model. The results describe the stated native
Linux namespace/veth/netem case study only.
