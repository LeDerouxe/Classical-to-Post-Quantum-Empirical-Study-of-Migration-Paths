# Windows 11 Validation Environment

This directory records the Windows environment used for the separate Step 4 cross-platform validation. It is not a replacement for the Ubuntu primary environment and its data will not be pooled with the Ubuntu campaign.

| Item | Recorded value |
| --- | --- |
| OS | Windows 11 Pro, version 10.0.26100, build 26100 |
| CPU | 12th Gen Intel Core i5-12450H; 8 cores, 12 logical processors |
| OpenSSL target | `VC-WIN64A` |
| OpenSSL version | 3.5.9 |
| OpenSSL source commit | `45e844fa2a14ec92d146bd8f5778ac130b6625fb` |
| Compiler | MSVC 19.44.35229 |
| Perl | Strawberry Perl 5.42.3 |
| Assembler | NASM 2.16.01 |
| Build configuration | `shared no-zlib` |

The native build is produced by [`build_openssl_windows.cmd`](../../scripts/setup/build_openssl_windows.cmd). The build tree and installation prefix are ignored local artifacts under `third_party/openssl-3.5.9/`.

The Windows build intentionally uses `no-zlib`, because no Windows zlib development dependency was introduced for this TLS 1.3 loopback study. This is recorded as a platform-build difference; it does not affect the configured TLS 1.3 handshake cases.

The feasibility gate was run while the active scheme was Balanced. It confirms implementation capability only. No performance data was collected under that scheme, and the main Windows campaign remains blocked until AC power, performance-oriented policy, and core-affinity gates have been recorded.
