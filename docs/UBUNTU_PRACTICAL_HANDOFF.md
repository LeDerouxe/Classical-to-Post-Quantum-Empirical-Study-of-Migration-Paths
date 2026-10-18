# Ubuntu Practical Handoff

## Purpose and stopping point

This document is the operational handoff for the Codex session running on the native Ubuntu 26.04.1 LTS installation. It covers **only Phase 0 and Phase 1** of the study.

Do not begin the pilot, performance benchmark, network emulation, Windows validation, or AMD validation in this handoff. After Phase 1, produce the requested report, commit non-sensitive artifacts, and wait for the researcher to review the findings with the planning session.

The research question is not "which algorithm is fastest?" The study evaluates a TLS 1.3/OpenSSL migration case study. Treat configuration-level effects and migration-path effects as distinct analytical units.

## Non-negotiable research decisions

| Topic | Decision |
| --- | --- |
| Primary OS | Native Ubuntu 26.04.1 LTS on Intel Core i5-12450H |
| Protocol | TLS 1.3 only |
| Primary implementation | Native OpenSSL 3.5.x; exact patch version and source commit must be pinned |
| OQS/liboqs | Not part of Phase 0 or Phase 1; do not install or mix it into primary results |
| Network | Loopback only during feasibility; no `tc/netem` yet |
| Certificates | Locally generated, non-production test certificates only; never commit private keys |
| Result status | Feasibility evidence only; do not report performance conclusions |

Repository documents that remain authoritative:

- `README.md`
- `docs/DECISIONS.md`
- `docs/EXPERIMENTAL_PROTOCOL.md`
- `docs/CITATION_POLICY.md`

## Required repository conventions

- Work in a native Linux filesystem directory, not an NTFS-mounted Windows directory.
- Clone the private GitHub repository in Ubuntu; do not copy Windows build outputs.
- Commit every meaningful, non-sensitive change with a descriptive message.
- Never commit private keys, certificate files, OpenSSL build trees, binaries, logs containing sensitive material, packet captures, or raw experiment data.
- Never overwrite raw data. This handoff should generate no benchmark data.
- Before performing system-wide package installation or any privileged action, explain the exact packages/action and request user approval.

## Phase map

| Phase | Name | Run now? | Gate to proceed |
| --- | --- | --- | --- |
| 0 | Environment preparation and registration | Yes | Manifest and pinned build evidence committed |
| 1 | TLS/OpenSSL feasibility validation | Yes, after Phase 0 | Report reviewed by researcher/planning session |
| 2 | Pilot measurements | No | Phase 1 results accepted and harness design approved |
| 3 | Primary benchmark | No | Pilot variance and instrumentation accepted |
| 4 | Network sensitivity with `tc/netem` | No | Primary benchmark plan accepted |
| 5 | Windows and AMD validation | No | Primary Ubuntu results accepted |

# Phase 0 — Environment preparation and registration

## P0.1 Repository and Git

1. Confirm the repository is the intended private GitHub repository and the working tree is clean before changing files.
2. Confirm `main` is the active branch.
3. Record the current Git commit hash in the environment manifest.
4. Configure a Git identity only if it is missing; do not guess or replace an existing identity.
5. Create only the directories needed for this phase, such as `environment/ubuntu-26.04.1/`, `configs/openssl/`, `scripts/setup/`, and `scripts/feasibility/`.

## P0.2 Tools to install or verify

First inspect what is already installed. If missing, request approval to install only the required packages:

- build toolchain: `build-essential`, `make`, `perl`, `git`, `pkg-config`
- OpenSSL build helpers: `cmake`, `ninja-build`, `zlib1g-dev`
- recording and automation: `python3`, `python3-venv`, `jq`, `coreutils`
- system and network inspection: `iproute2`, `sysstat`, `linux-tools-common`, `linux-tools-$(uname -r)`, `tcpdump`

`tshark`, Wireshark, `h2load`, Docker, Valgrind, OQS/liboqs, and performance-tuning packages are **not required now**. Add them later only if the approved measurement design requires them.

## P0.3 Environment manifest

Create a version-controlled, human-readable manifest at:

`environment/ubuntu-26.04.1/environment-manifest.md`

It must record the following with command outputs or exact values:

- collection date and local timezone;
- Ubuntu release and kernel;
- hostname only if the researcher permits it; otherwise use a stable pseudonym such as `primary-i5`;
- CPU model, core/topology information, microcode if available, and RAM;
- storage filesystem type for the repository;
- CPU governor/energy-performance preference and AC-power status;
- relevant background load at collection time;
- GCC, Make, CMake, Ninja, Python, Git, and package-manager versions;
- exact OpenSSL version, upstream Git tag, source commit hash, build command, compiler, and build flags;
- repository commit hash;
- an explicit statement that the platform is native Ubuntu 26.04.1 on the Intel Core i5-12450H.

Do not change CPU governor, power mode, BIOS settings, swap policy, or kernel settings in Phase 0. First record the default state. Any future change must be an explicit documented experimental control.

## P0.4 Build the research OpenSSL

1. Do not use the system OpenSSL package as the primary research binary.
2. Consult the official OpenSSL release/source record and select the latest appropriate stable patch release in the 3.5 LTS series at setup time.
3. Download or clone from the official OpenSSL source only. Verify the selected tag and record its commit identifier and any available integrity evidence.
4. Build a separate, local research installation under a repository-local ignored directory such as `third_party/openssl-<exact-version>/install/` or an equivalent location outside the repository.
5. Do not overwrite `/usr/bin/openssl`, system libraries, or system TLS configuration.
6. Use the resulting binary through an explicit absolute path or a controlled environment variable in every later script; never rely on whichever `openssl` is first on `PATH`.
7. Record the complete build command and `openssl version -a` output in the manifest.

Recommended build properties, subject to the OpenSSL version's supported options:

- shared-library build suitable for `s_server` and `s_client` testing;
- no special CPU architecture optimization flags beyond the documented default unless later approved;
- a clearly recorded install prefix;
- no FIPS claim and no production deployment claim.

## P0.5 OpenSSL inventory

Using the research binary, capture and save a short inventory in `environment/ubuntu-26.04.1/openssl-inventory.txt`:

- `openssl version -a`;
- available TLS groups;
- available signature algorithms;
- available public-key algorithms/providers;
- a check for ML-KEM, ML-DSA, `X25519`, and `X25519MLKEM768` names exactly as exposed by that build.

Do not assume algorithm spelling from this document. The actual names returned by the pinned binary are the source of truth for subsequent commands and configurations.

## P0.6 Phase 0 deliverables

Commit only non-sensitive material:

- environment manifest;
- reproducible setup/build script or documented build procedure;
- OpenSSL inventory;
- `.gitignore` updates needed to protect build output and generated credentials.

Suggested commit message:

`Record Ubuntu environment and pin research OpenSSL build`

Then report: the exact OpenSSL version and commit, whether ML-KEM/ML-DSA/hybrid groups are listed, tool versions, manifest path, and Git commit hash.

# Phase 1 — TLS/OpenSSL feasibility validation

## Objective

Determine which candidate TLS 1.3 configurations can complete a reproducible local handshake with the pinned native OpenSSL build. This is a compatibility check, not a speed test.

## Test topology and controls

- Use loopback only: server and client on the same Ubuntu host.
- Force TLS 1.3 only.
- Use a single fixed TLS 1.3 cipher suite chosen once and documented.
- Disable resumption/session reuse in feasibility commands so every observation is a full handshake.
- Use locally generated self-signed test certificates. Do not use a real domain, CA certificate, production key, or internet-facing server.
- Keep the server/client commands and certificate-generation commands under version control, but keep generated keys and certificates ignored.
- Start each trial with a fresh server process when practical, so a configuration cannot inherit state from another configuration.

## Candidate matrix

| ID | Key establishment | Authentication | Expected interpretation |
| --- | --- | --- | --- |
| S0 | X25519 | ECDSA | Classical control; must succeed before testing other rows |
| S2 | X25519MLKEM768 | ECDSA | Hybrid key-establishment candidate |
| S3 | X25519MLKEM768 | ML-DSA-65 | Hybrid KEM with PQ authentication candidate |
| S4 | ML-KEM-768 if directly supported as a TLS group | ML-DSA-65 | Exploratory pure-PQ candidate; failure is expected to be possible |

Important: RFC 10024 defines standardized **hybrid** TLS groups. Do not infer that a standalone ML-KEM TLS group is standardized or offered by the selected OpenSSL build. If S4 is unavailable, record it as unavailable and do not force a workaround merely to fill the table.

## P1.1 Generate and inspect test credentials

1. Discover the exact key/signature names from the P0.5 inventory.
2. Generate a short-lived ECDSA test certificate for S0 and S2.
3. Attempt a short-lived ML-DSA test certificate only if the research binary exposes the necessary generation and X.509/TLS support.
4. Inspect each certificate with the research binary and record its public-key algorithm, signature algorithm, validity period, and file checksum. Do not commit the certificate or private key.
5. If ML-DSA certificate creation fails, preserve the exact command and relevant error output as a feasibility finding.

## P1.2 Execute feasibility cases

For each case, write scripts/configuration files that invoke the research binary by absolute path.

For every configuration:

1. Start a TLS 1.3 `s_server` using the corresponding test credential and explicit group/signature settings derived from the P0.5 inventory.
2. Run a TLS 1.3 `s_client` against loopback with the matching explicit group/signature settings.
3. Verify the following from client/server output:
   - TLS 1.3 was negotiated;
   - the intended group was negotiated, or document the negotiated group if fallback occurred;
   - the intended certificate/public-key and signature algorithms were used where applicable;
   - handshake success or a precise failure reason;
   - no unexpected fallback to a classical group or older TLS version occurred.
4. Repeat the same case **three times** as separate fresh handshakes. A case is feasible only when all three runs show the intended behavior.
5. Save a per-run log and a compact summary row. Logs remain ignored; a sanitized summary is version controlled.

Never silently substitute an available algorithm for the requested one. If a configuration falls back or fails, its status is `fallback` or `failed`, not `passed`.

## P1.3 Feasibility result schema

Create `docs/FEASIBILITY_RESULTS.md` with one row per candidate. Use exactly these fields:

| Case ID | Requested group | Observed group | Requested certificate/key type | Observed certificate/key type | TLS version | Runs passed / 3 | Status | Evidence log path | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Allowed values for **Status**: `passed`, `failed`, `fallback`, `unavailable`, `blocked`.

Use `blocked` only for a genuine unresolved environment problem. Do not use it merely because a configuration is difficult or unavailable.

## P1.4 Stop condition and report

After S0/S2/S3/S4 have each been attempted and the result table is complete:

1. Commit non-sensitive scripts, configuration templates, and `docs/FEASIBILITY_RESULTS.md`.
2. Do not start Phase 2.
3. Report back to the researcher with:
   - repository URL/path and final Git commit hash;
   - exact pinned OpenSSL version, tag, and source commit;
   - a one-line result for S0, S2, S3, and S4;
   - the exact reason for each failed, fallback, unavailable, or blocked case;
   - confirmation that no benchmark/pilot/network experiment was run.

Suggested commit message:

`Validate TLS 1.3 candidate configurations`

# What happens after this handoff

The researcher will review the Phase 1 report and then decide the final benchmark matrix. Only then may Phase 2 begin:

- **Phase 2 pilot:** 10 warm-up runs plus 30 measured runs per feasible configuration. Collect only handshake latency, success/failure, CPU time or utilization, peak RSS, handshake bytes, and packet count. Inspect variance and measurement overhead.
- **Phase 3 primary benchmark:** at least 50 repetitions per approved configuration/condition; randomized order; median, P50, P95, P99, dispersion, and confidence intervals.
- **Phase 4 network sensitivity:** native Linux `tc/netem`, first RTT 1/10/50/100 ms with 0% loss, then conditional loss experiments.
- **Phase 5 validation:** selected subset on Windows 11 on the same i5, then selected subset on Ubuntu/AMD A10.

No phase may be skipped or started early without explicit researcher approval.
