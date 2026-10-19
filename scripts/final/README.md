# Final Ubuntu measurement workflow

This is a separate final-measurement workflow. It reuses the reviewed `scripts/pilot/tls_pilot.c` harness and observation helper without editing or writing to the pilot workflow, pilot configuration, pilot CSVs, or pilot metadata.

## Preflight only

From the repository root run:

```bash
python3 scripts/final/run_final.py --preflight-only
```

Preflight compiles the harness into ignored `build/final/`, checks the pinned OpenSSL 3.5.9 source commit and local shared-library linkage, validates the configured credentials without printing key material, inspects CPU topology and power state, inventories prior campaigns, and records evidence under `evidence/final-workflow/`. It never creates a final raw CSV. It exits nonzero and reports `ready_to_collect: false` if AC, power or platform profile, any governor/EPP, topology, credentials, OpenSSL, or compilation checks fail. It does not change power settings. Existing final campaigns are reported and do not by themselves fail preflight.

## Smoke test

Run `python3 scripts/final/run_final.py --smoke-test` to apply the same host, OpenSSL, credential, topology, AC, power profile, platform profile, governor, and EPP guards, then perform exactly one fresh loopback handshake for S0, S2, S3, and S4 with the compiled final harness. It verifies negotiated TLS 1.3, cipher, group, signature, success, and positive client-side `TCP_INFO` byte/packet counters. The smoke report is written under `evidence/final-workflow/`; the CSV and benchmark-metadata inventory must be unchanged. Smoke does not create a final CSV, final benchmark metadata, or benchmark dataset.

## Run gate and immutable batch files

`python3 scripts/final/run_final.py --run` is the distinct collection command. Every invocation assigns a unique `campaign_id`, performs the preflight guards again, and refuses collection if any guard fails. It places that campaign's files in its own directories under `data/raw/final/<campaign_id>/` and `data/metadata/final/<campaign_id>/`. It never resumes or merges an earlier campaign; a later invocation always starts with a new ID, including after an incomplete campaign. The final config specifies five batches of S0/S2/S3/S4, with 10 warm-ups per case and 30 measured handshakes per case. A master seed deterministically derives and records one seed per batch. Warm-ups are shuffled separately; all 120 measured observations are fully shuffled together within each batch.

Each batch writes a new exclusive CSV and metadata JSON within the campaign directories. Outputs are never overwritten or resumed. Rows are flushed as they are collected; errors and interruptions leave an explicitly `incomplete` metadata record and preserve any partial CSV. Successful CSV and metadata files become read-only. The run records batch start/end snapshots of AC/battery, profiles, per-policy governor/EPP, frequencies, topology, target affinity, load, thermal zones, and top process names/CPU use. It also records source/config/harness identities, planned and realized order, timestamps, seeds, and the 120-second idle interval before each batch after the first. No power policy is changed by this workflow.

No final benchmark batches have been run as part of this preparation.
