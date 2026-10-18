# Phase 2 Pilot

This directory contains the Phase 2 pilot protocol. The harness and fixed configuration are in `scripts/pilot/` and `configs/pilot/`.

## Prepare and run

1. Confirm Phase 0/1 acceptance and review [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md).
2. Ensure the ignored local OpenSSL build exists at `third_party/openssl-3.5.9/install/`.
3. Ensure ignored local files `credentials/ecdsa.cert.pem`, `credentials/ecdsa.key.pem`, `credentials/mldsa.cert.pem`, and `credentials/mldsa.key.pem` exist. Never commit these files.
4. Confirm the candidate CPU mapping and choices in `configs/pilot/pilot.json` are valid for this host. Do not change power policy as part of this pilot.
5. From the repository root, run `python3 scripts/pilot/run_pilot.py`.

The runner compiles the C harness, performs the configured warm-ups and randomized measurements, and creates one immutable CSV plus a metadata JSON. It does not overwrite prior runs. Review a completed run using its checksum and metadata; see the protocol for column and instrumentation definitions.

## Outputs

- Raw rows: `data/raw/pilot/<run-id>.csv` (all 40 warm-ups and 120 measured rows; raw data is ignored by default until reviewed).
- Run metadata: `data/metadata/pilot/<run-id>.json`.
- Harness source: `scripts/pilot/tls_pilot.c`.

Do not begin Phase 3 until the pilot has been reviewed and explicitly accepted.
