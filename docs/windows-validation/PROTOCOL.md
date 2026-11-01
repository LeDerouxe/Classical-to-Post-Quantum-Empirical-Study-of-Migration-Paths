# Windows Validation Protocol

## Purpose and boundary

This study is the Step 4 cross-platform validation in the project roadmap. It
tests whether the within-platform latency contrasts observed on Ubuntu have the
same direction on Windows 11 running on the same Intel Core i5-12450H. It is a
separate campaign: Windows observations will not be pooled with Ubuntu
observations, and it does not establish a general operating-system comparison.

The study uses all four completed primary configurations (S0, S2, S3, and S4).
The primary Windows endpoint is fresh-handshake latency around `SSL_connect()`.
Linux `TCP_INFO` communication fields and Linux `getrusage` resource fields are
not replicated unless a separately validated Windows-equivalent method is
added. The validation therefore addresses the direction of latency contrasts,
not equality of absolute times or of secondary metrics.

## Fixed implementation boundary

- Native Windows 11 Pro, build and hardware identity recorded at preflight.
- Intel Core i5-12450H, the same physical machine used by the Ubuntu primary
  campaign.
- Native Windows build of OpenSSL 3.5.9 from source commit
  `45e844fa2a14ec92d146bd8f5778ac130b6625fb`.
- TLS 1.3 only and `TLS_AES_128_GCM_SHA256` only.
- S0: X25519 / ECDSA P-256; S2: X25519MLKEM768 / ECDSA P-256; S3:
  X25519MLKEM768 / ML-DSA-65; S4: MLKEM768 / ML-DSA-65.
- Fresh client and one-accept server processes for every handshake; session
  tickets, resumption, and session caches disabled.

S4 remains an implementation-supported pure-PQ configuration in the pinned
build, not a standardized RFC 10024 hybrid group.

## Toolchain gate

The following tools are required before building OpenSSL or compiling the
Windows harness:

- Visual Studio Build Tools 2022 with the C++ build-tools workload and a
  Windows SDK;
- Strawberry Perl;
- NASM.

The verified WinGet package identifiers are
`Microsoft.VisualStudio.2022.BuildTools`, `StrawberryPerl.StrawberryPerl`, and
`NASM.NASM`. Installation is not part of data collection. The preflight must
record tool paths and versions, the OpenSSL configure command, source commit,
build options, executable/library identity, and enabled group/signature
inventory. A system OpenSSL executable is not an acceptable substitute.

## Environment and topology gate

Before every batch, record:

- AC/battery state and active power-scheme GUID;
- Windows version and build, CPU model, logical-processor topology, and the
  selected process-affinity masks;
- a short background-process and load snapshot;
- local repository commit, OpenSSL source commit, binary hashes, and test
  credential hashes.

The campaign must use AC power and an explicitly recorded performance-oriented
power policy. The workflow must not change a power policy automatically. The
researcher applies the selected policy before collection; preflight then
confirms it. The native harness must select two non-sibling performance cores
from the recorded Windows processor topology and pin the client and server to
those cores. If the topology cannot justify that selection, collection stops.

## Feasibility and smoke gates

1. Build the pinned native OpenSSL installation and the Windows harness.
2. Confirm the requested TLS group, certificate public-key type, and
   CertificateVerify signature for three fresh feasibility handshakes per S0,
   S2, S3, and S4.
3. Generate local, ignored Windows-validation credentials with SAN hostnames;
   record their hashes and validity. Do not reuse or overwrite Ubuntu
   credentials.
4. Under the collection environment guards, run one fresh smoke handshake per
   case. Record configuration validation and the `QueryPerformanceCounter`
   timing boundary, but create no campaign data.

Any gate failure is retained as separate evidence and blocks the main campaign
until its cause is understood. It is not repaired by silently changing the
recorded configuration.

## Main collection

The main campaign uses five batches. Each batch contains ten retained warm-ups
and thirty measured fresh handshakes for every case. The four-case measured
order is randomized within each batch with a recorded seed. The campaign thus
contains 200 warm-ups and 600 measured observations, or 150 measured
observations per case.

The timing value is the `QueryPerformanceCounter` interval immediately around
the client `SSL_connect()` call. Each row records the case, batch and sequence
identifiers, warm-up flag, timestamp, timing value, configuration-validation
fields, client/server exit status, selected CPU affinity, and sanitized errors.
Metadata records the preflight and post-batch environment snapshots. Raw output
is written once to a new campaign directory under `data/raw/windows/`; matching
metadata and checksums are written under `data/metadata/windows/`.

No successful observation is removed as an outlier. Failed handshakes, partial
batches, and policy deviations are retained and reported. A completed batch is
never overwritten or resumed.

## Analysis and interpretation

For Windows, summarize latency by case and batch using median and IQR. Report
within-Windows contrasts as median(case) minus median(S0), their direction in
each batch, and a recorded bootstrap procedure. Compare contrast directions
with Ubuntu qualitatively; do not pool raw observations, test a Windows-minus-
Ubuntu absolute-time difference, or claim a general OS effect.

The final report must distinguish platform validation from the Ubuntu primary
results and state the incomplete scope: one device, one Windows build, one
OpenSSL build, loopback transport, local test credentials, and no browser or
public-PKI interoperability claim.
