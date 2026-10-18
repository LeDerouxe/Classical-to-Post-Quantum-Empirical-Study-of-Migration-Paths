# Phase 2B Stabilization Report

## Run record

- Run ID: `pilot-20261018T191843Z-e9dd8f86`
- Collection commit: `c52a43bab30d5776776d9a37705d30ae95244212`
- OpenSSL: 3.5.9, source commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb`
- Cases: S0, S2, S3, S4; 10 warm-ups and 30 measured fresh handshakes per case; measured order randomized.
- All 160 handshakes succeeded and the requested TLS version, cipher suite, group, and signature scheme matched.
- Client/server CPUs: 2 and 4, distinct P-cores; CPU 0 left available to the OS.
- Raw CSV: `data/raw/pilot/pilot-20261018T191843Z-e9dd8f86.csv` (60,290 bytes)
- Run metadata: `data/metadata/pilot/pilot-20261018T191843Z-e9dd8f86.json`
- CSV SHA-256: `016b3e73e25a9403b03b246984aa83b66d5873052b974756fd973784a881397d`

## Measurement stability and variance

Latency spread is reported as standard deviation and coefficient of variation (CV). The final column counts points beyond 1.5×IQR fences; sequence indices refer to the full CSV.

| Case | Phase 2 CV | Phase 2B SD (ms) | Phase 2B CV | Phase 2B range (ms) | 1.5×IQR outliers |
|---|---:|---:|---:|---:|---:|
| S0 | 9.7% | 0.169 | 18.6% | 0.703–1.467 | 3: 43 (1.251), 44 (1.297), 145 (1.467) |
| S2 | 35.7% | 0.145 | 13.5% | 0.887–1.601 | 1: 104 (1.601) |
| S3 | 43.2% | 0.679 | 39.6% | 1.077–4.124 | 2: 131 (4.124), 154 (3.273) |
| S4 | 40.4% | 0.623 | 39.1% | 0.916–3.007 | 0 |

These figures describe run-to-run spread only; they do not support performance conclusions.

## Environmental conditions and changes

- The recorded initial state had AC disconnected, battery at 54% and discharging, profile/platform profile `balanced`, governor `powersave`, and EPP `balance_power`.
- After explicit user approval and AC connection, the recorded commands were `powerprofilesctl set performance` and `sudo cpupower frequency-set -g performance`. Before and after the batch, AC remained online, the battery remained charging, and system/platform profile, governor, and EPP were all `performance` across all CPU policies. Frequency minimum/maximum limits were unchanged.
- Batch-start and batch-end load averages were effectively unchanged at 0.75/0.79/0.52. Available `TCPU_PCI` and package thermal zones rose from 43 °C to 52 °C; `acpitz` remained 39 °C. No per-core thermal sensor was available.
- Instantaneous CPU-frequency snapshots varied across CPUs despite the stable policy: P-core readings ranged from 0.4 to 4.1 GHz and E-core readings from about 1.3 to 3.3 GHz across the two snapshots. These are before/after snapshots, not continuous telemetry.
- The desktop snapshot showed ChatGPT/Codex, GNOME Shell, and Xwayland activity at both boundaries; Firefox was no longer present. No `tcpdump` process remained.
- The prior Phase 2 CSV and [Phase 2 report](PILOT_REPORT.md) remain unchanged. The new CSV SHA-256 matches the run metadata.

Phase 2B is diagnostic stability evidence only. Do not draw performance conclusions or start Phase 3.
