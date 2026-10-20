# Migration Effort Record

## Purpose and boundary

This record operationalizes migration effort for the TLS 1.3/OpenSSL case
study. It is not a score, an estimate of organization-wide effort, or a
stateful deployment simulation. A TLS handshake has a cryptographic
configuration, not a memory of the route used to reach it. Consequently,
runtime and communication measurements remain configuration-level results,
while this record documents the configuration changes and compatibility
evidence associated with two analytical migration paths.

The record uses the final configuration matrix at repository commit
`d03163e`. It does not infer effort from lines of code, assign arbitrary
weights, or reconstruct elapsed human migration time retrospectively.

## Evidence basis

- `configs/final/final.json` is the authoritative final case matrix.
- `scripts/pilot/tls_pilot.c` is a parameterized, shared client/server
  harness. It receives the group, signature algorithm, certificate/key path,
  trust certificate, and hostname as runtime inputs; it was not edited between
  cases.
- `docs/phase-1/FEASIBILITY_RESULTS.md` records three successful fresh TLS
  1.3 handshakes for each configuration.
- The final Ubuntu campaign contains 150 measured successful handshakes for
  each configuration under the same pinned OpenSSL 3.5.9 build. Its integrity
  conditions and scope are recorded in
  `docs/phase-2/FINAL-CAMPAIGN-INTEGRITY-20261020.md`.

## Fixed common environment

All transitions use the same native OpenSSL 3.5.9 source commit
`45e844fa2a14ec92d146bd8f5778ac130b6625fb`, TLS 1.3, cipher suite
`TLS_AES_128_GCM_SHA256`, default provider configuration, fresh-handshake
policy, disabled tickets/session cache, and shared benchmark harness.

Provisioning a PQ-capable OpenSSL build was a one-time environment
precondition for this case study. It is not attributed repeatedly to each
transition. No transition changed a source dependency, compiler/build flag,
TLS version, cipher suite, harness source file, or benchmark workflow.

## Configuration states

| State | Key-establishment group | Signature scheme | Credential and trust material | Hostname |
| --- | --- | --- | --- | --- |
| S0 | `x25519` | `ecdsa_secp256r1_sha256` | ECDSA certificate and key; ECDSA trust certificate | `ecdsa.localhost` |
| S2 | `X25519MLKEM768` | `ecdsa_secp256r1_sha256` | ECDSA certificate and key; ECDSA trust certificate | `ecdsa.localhost` |
| S3 | `X25519MLKEM768` | `mldsa65` | ML-DSA certificate and key; ML-DSA trust certificate | `mldsa.localhost` |
| S4 | `MLKEM768` | `mldsa65` | ML-DSA certificate and key; ML-DSA trust certificate | `mldsa.localhost` |

S4 is an OpenSSL implementation-supported pure-PQ configuration in this
case study. It is not described as an RFC 10024 hybrid group.

## Atomic transition records

| Transition | Required configuration changes | Harness or build change | Case-specific verification | Compatibility evidence | Measured migration time |
| --- | --- | --- | --- | --- | --- |
| S0 to S2 | Replace the group value `x25519` with `X25519MLKEM768`. Keep signature, credential/trust material, and hostname unchanged. | None. | Set the S2 group input and run the existing validation workflow. | S2: feasibility 3/3; final campaign 150/150 measured successes. | Not measured. |
| S2 to S3 | Replace signature `ecdsa_secp256r1_sha256` with `mldsa65`; replace ECDSA certificate/key and trust certificate with the ML-DSA pair; replace hostname `ecdsa.localhost` with `mldsa.localhost`. Keep the hybrid group unchanged. | None. | Set the S3 signature, credential, trust, and hostname inputs and run the existing validation workflow. | S3: feasibility 3/3; final campaign 150/150 measured successes. | Not measured. |
| S3 to S4 | Replace group `X25519MLKEM768` with `MLKEM768`. Keep ML-DSA signature, credential/trust material, and hostname unchanged. | None. | Set the S4 group input and run the existing validation workflow. | S4: feasibility 3/3; final campaign 150/150 measured successes. | Not measured. |

`None` in the harness/build column means no change within this controlled
repository and pinned implementation. It must not be generalized to other
applications, PKI arrangements, deployment automation, or hardware.

## Path-level synthesis

### Direct path: S0 to S4

The direct path combines the S0-to-S2 group replacement, the S2-to-S3
authentication and credential/trust replacement, and the S3-to-S4 group
replacement into one cutover. Its observable final-state changes are:

1. group: `x25519` to `MLKEM768`;
2. signature: ECDSA P-256 to ML-DSA-65;
3. certificate/key and client trust anchor: ECDSA material to ML-DSA material;
4. hostname used for certificate validation: `ecdsa.localhost` to
   `mldsa.localhost`.

The final S4 endpoint passed the recorded feasibility and final-campaign
checks. This is endpoint configuration evidence, not evidence that an S0-only
peer interoperates with S4 or that a production cutover has no operational
risk.

### Staged path: S0 to S2 to S3 to S4

The staged path exposes three independently validated configuration changes:

1. hybrid key establishment while retaining ECDSA authentication;
2. PQ authentication and associated credential/trust transition while
   retaining the hybrid group;
3. replacement of the hybrid group with the pure-PQ `MLKEM768` group.

Within this repository, staging does not require source-code or build changes
between steps. Its analytical value is that it isolates which configuration
inputs and endpoint compatibility checks change at each transition.

## Compatibility, failures, and unmeasured dimensions

The available evidence establishes successful handshakes when client and
server are configured for the same listed state. It does **not** measure:

- mixed-version client/server interoperability or fallback behavior;
- external-client compatibility;
- certificate issuance, revocation, distribution, or PKI operational work;
- application API refactoring outside this parameterized harness;
- human labor time, downtime, rollback time, or recovery time;
- deployment risk in a production service.

No case-specific handshake failure or recovery event was recorded in the
Phase 1 feasibility evidence or the final Ubuntu campaign. This means only
that none occurred in the tested compatible endpoint pairs; it is not a claim
that migration cannot fail elsewhere.

## Reporting rule

The manuscript may report these as raw, case-specific migration descriptors.
It must not combine them into a migration-effort index or claim that the
record predicts effort for other TLS deployments.
