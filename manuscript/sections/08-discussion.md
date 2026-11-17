# 8 Discussion

## 8.1 Interpreting the configuration contrasts

The primary result is a within-environment ordering, rather than a general
ranking of TLS implementations. In the Ubuntu loopback study, all three
non-classical configurations had a positive median `SSL_connect()` contrast
relative to S0 in each retained batch. The smallest contrast was observed for
S2, which changes the key-establishment group while retaining ECDSA P-256
authentication. The larger contrasts for S3 and S4 occurred in configurations
using ML-DSA-65 authentication. The study design does not identify which
operation, representation, or implementation detail causes those differences;
it supports only the configuration-level contrasts measured at the stated
handshake boundary.

The communication descriptors give useful but limited context. Relative to S0,
S2 increased the median handshake byte count while retaining the same median
packet count in the loopback campaign. S3 and S4 had substantially higher
median byte counts and four additional median packets. These descriptors are
not a decomposition of latency and do not establish a causal contribution of
packetization, certificate material, or cryptographic computation. They do,
however, show that the cases differ in more than a single scalar timing value
at the measured boundary.

## 8.2 Implications for an evaluated migration path

The staged S0-to-S2-to-S3-to-S4 record separates two questions that are often
conflated in migration discussions. The S0-to-S2 transition changes the
key-establishment group; S2-to-S3 changes authentication and associated
credential, trust, and hostname material; S3-to-S4 changes the group again.
The direct S0-to-S4 path combines those changes. This record makes the
configuration changes auditable, but it is not a measurement of organizational
effort, PKI operations, rollback, or deployment risk.

The compatibility follow-up adds local functional evidence to that record. In
the pinned native OpenSSL environment, the D profile completed all three
attempts with L, H, D, and Q, while Q had no common group with L or H. Thus,
the defined D profile was a bridge across the profiles evaluated here. This is
useful evidence for the local transition design, not evidence that a
dual-capable configuration will bridge browsers, public trust stores, other TLS
libraries, or production policy constraints. It also does not settle the
operational security policy that should govern a temporary dual-capable phase.

## 8.3 Network conditions change the practical picture

The network follow-up preserves the direction of the configuration contrasts
but changes their practical scale. Under the fixed symmetric-delay topology,
S2 remained close to S0 at 10, 50, and 100 ms added RTT. At the same
conditions, S3 and S4 had contrasts close to one added RTT. The latter pattern
appeared alongside higher retained TCP_INFO packet counts for S3 and S4 than
for S0 and S2. A plausible implementation-level interpretation is that the
observed handshake exchange interacts with the imposed delay differently for
those cases. The experiment cannot isolate that mechanism, and it did not
test loss, jitter, bandwidth limits, congestion, reordering, middleboxes, or
Internet paths.

The 0-ms namespace condition should likewise not be treated as a replication
of the primary loopback result. It uses a distinct topology and is included as
the control condition for the network campaign. The two campaigns answer
different questions and are reported without pooling.

## 8.4 Cross-platform interpretation

The Windows follow-up strengthens the narrow conclusion that the observed
within-platform directions were not unique to one operating-system execution
of this harness on the tested hardware. S2, S3, and S4 again had positive
contrasts relative to S0 in every Windows batch, with the same ordering of
case medians as in Ubuntu. This directional agreement is deliberately weaker
than an operating-system comparison. The timing implementations, transport
instrumentation, and surrounding runtime environment differed, so no absolute
Windows-minus-Ubuntu latency effect was estimated. Linux-only TCP_INFO and
resource descriptors were also not reproduced on Windows.

## 8.5 Practical reading of the evidence

For this case study, the evidence favors an incremental interpretation of S2
over a claim that all post-quantum configurations have comparable local cost.
It also indicates that authentication changes matter in the selected
configurations, and that their observed practical impact can be more visible
when a controlled RTT is introduced. A deployment decision still requires
evidence outside this study: the supported TLS implementations of real peers,
certificate and trust-store policy, target network conditions, application
traffic, security requirements, and a rollback plan. The value of the present
study is the auditable separation of these questions, not a universal migration
prescription.
