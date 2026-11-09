# Windows Feasibility Results

The Windows feasibility gate used the pinned native OpenSSL 3.5.9 build on the same Intel Core i5-12450H as the Ubuntu primary campaign. It consisted of three fresh loopback handshakes for each configuration. This was a capability check, not a performance measurement.

| Case | Requested group | Authentication | Result |
| --- | --- | --- | --- |
| S0 | `x25519` | ECDSA P-256 / `ecdsa_secp256r1_sha256` | passed, 3/3 |
| S2 | `X25519MLKEM768` | ECDSA P-256 / `ecdsa_secp256r1_sha256` | passed, 3/3 |
| S3 | `X25519MLKEM768` | ML-DSA-65 / `mldsa65` | passed, 3/3 |
| S4 | `MLKEM768` | ML-DSA-65 / `mldsa65` | passed, 3/3 |

Every passing record negotiated TLS 1.3 and `TLS_AES_128_GCM_SHA256`, and passed certificate-chain and hostname verification. Credentials were generated in the ignored local directory `credentials/windows-validation/` with SAN hostnames `ecdsa.localhost` and `mldsa.localhost`. The certificate SHA-256 values were `9cb678fac0f299da442b37e4d86791397ddca5310a2664077df88fc998d6a6a3` and `f6308a60da603aeb16f76fd28f9a2173d76f8c0526a6448038bf732472b91949`, respectively.

The feasibility commands wrote local logs under `logs/windows-feasibility/`. Those logs, private keys, certificates, the temporary harness binary, and the OpenSSL build outputs are intentionally ignored. The portable source for the Windows harness is `scripts/windows/tls_windows.c`.

No Windows performance campaign, smoke campaign, or comparative analysis has been run. The active power scheme during feasibility was Balanced; therefore the observed `QueryPerformanceCounter` values are not reported as timing results.
