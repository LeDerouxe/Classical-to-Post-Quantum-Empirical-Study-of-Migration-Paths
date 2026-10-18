# Phase 2 Pilot

This directory contains documentation for the original Phase 2 diagnostic pilot and the separate Phase 2B stabilization pilot. The original Phase 2 used client/server CPUs 0/2 and left the power policy unchanged. Phase 2B used CPUs 2/4 under the explicitly approved performance profile, governor, and EPP policy. These are distinct historical runs; see [PHASE-2B-STABILIZATION.md](PHASE-2B-STABILIZATION.md). The harness and fixed configuration are in `scripts/pilot/` and `configs/pilot/`.

## Prepare and run

1. Confirm Phase 0/1 acceptance and review [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md).
2. Ensure the ignored local OpenSSL build exists at `third_party/openssl-3.5.9/install/`.
3. Ensure ignored local files `credentials/ecdsa.cert.pem`, `credentials/ecdsa.key.pem`, `credentials/mldsa.cert.pem`, and `credentials/mldsa.key.pem` exist. Never commit these files.
4. The instructions above describe the original Phase 2 run only. For the historical Phase 2B run, CPUs 2/4 and the approved performance policy are documented separately. The proposed final design is not an execution authorization; follow its review gate before any new measurements.
5. From the repository root, run `python3 scripts/pilot/run_pilot.py`.

The runner compiles the C harness, performs the configured warm-ups and randomized measurements, and creates one immutable CSV plus a metadata JSON. It does not overwrite prior runs. Review a completed run using its checksum and metadata; see the protocol for column and instrumentation definitions.

## Outputs

- Raw rows: `data/raw/pilot/<run-id>.csv` (all 40 warm-ups and 120 measured rows; raw data is ignored by default until reviewed).
- Run metadata: `data/metadata/pilot/<run-id>.json`.
- Harness source: `scripts/pilot/tls_pilot.c`.

Do not begin Phase 3 until the pilot has been reviewed and explicitly accepted.
