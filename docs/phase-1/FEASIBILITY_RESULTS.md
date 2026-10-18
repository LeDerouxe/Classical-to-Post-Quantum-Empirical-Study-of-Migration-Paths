# TLS 1.3 Feasibility Results

Feasibility evidence only; no performance or pilot measurements were run.
All cases used TLS_AES_128_GCM_SHA256. Requested group spellings follow `openssl list -tls-groups`; this build exposes the standalone ML-KEM-768 group as `MLKEM768`.

| Case ID | Requested group | Observed group | Requested certificate/key type | Observed certificate/key type | TLS version | Runs passed / 3 | Status | Evidence log path | Notes |
|---|---|---|---|---|---|---|---|---|---|
| S0 | x25519 | X25519, 253 bits | ECDSA | ECDSA | TLSv1.3 | 3 | passed | logs/feasibility/S0-run*.log | All three fresh TLS 1.3 handshakes verified TLS_AES_128_GCM_SHA256, the requested group, certificate, and signature type. Certificate SHA-256: 7f21df9840134a890c5fc22e303016ebd1488f61266f712dd2ba787510a7bdda. |
| S2 | X25519MLKEM768 | X25519MLKEM768 | ECDSA | ECDSA | TLSv1.3 | 3 | passed | logs/feasibility/S2-run*.log | All three fresh TLS 1.3 handshakes verified TLS_AES_128_GCM_SHA256, the requested group, certificate, and signature type. Certificate SHA-256: 7f21df9840134a890c5fc22e303016ebd1488f61266f712dd2ba787510a7bdda. |
| S3 | X25519MLKEM768 | X25519MLKEM768 | ML-DSA-65 | ML-DSA-65 | TLSv1.3 | 3 | passed | logs/feasibility/S3-run*.log | All three fresh TLS 1.3 handshakes verified TLS_AES_128_GCM_SHA256, the requested group, certificate, and signature type. Certificate SHA-256: 2b59eabd04080a6f2245f582dc3b3bc8d51d430f6c6f8d916b55662c7b8b8b3e. |
| S4 | MLKEM768 | MLKEM768 | ML-DSA-65 | ML-DSA-65 | TLSv1.3 | 3 | passed | logs/feasibility/S4-run*.log | All three fresh TLS 1.3 handshakes verified TLS_AES_128_GCM_SHA256, the requested group, certificate, and signature type. Certificate SHA-256: 2b59eabd04080a6f2245f582dc3b3bc8d51d430f6c6f8d916b55662c7b8b8b3e. |
