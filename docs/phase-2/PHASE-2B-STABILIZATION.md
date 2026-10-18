# Phase 2B Stabilization Pilot

## Purpose and limits

Phase 2B repeats the diagnostic pilot to assess measurement stability and within-case variance under a documented, stable operating environment. It does not authorize Phase 3 or performance conclusions. The Phase 2 CSV and report remain immutable and unchanged.

## Preflight snapshot

The initial preflight was captured in `data/metadata/pilot/phase2b-preflight-20261018.json`; no Phase 2B handshake data was collected at that point.

- Topology: P-core sibling pairs are 0/1, 2/3, 4/5, and 6/7; CPUs 8–11 are E-cores. Use client CPU 2 and server CPU 4, which are non-siblings and leave CPU 0 available to the OS.
- Initial policy: `powerprofilesctl` profile `balanced`, platform profile `balanced`, governor `powersave`, EPP `balance_power`.
- Initial power: AC adapter offline; battery discharging at 54%.
- Initial thermal readings: available ACPI/CPU/package zones around 34–36 °C. No per-core thermal sensor was exposed.
- Initial load average and CPU frequencies are recorded in the preflight JSON. The initial desktop process snapshot showed ChatGPT, Firefox, GNOME Shell, Xwayland and browser helper processes active.

## Approval gate and intended policy

Do not change governor, EPP, performance mode, or any system-wide power setting until the user explicitly approves. AC must be connected before applying a power policy or collecting data. Close other unnecessary high-CPU desktop/background applications before collection; leave the Codex session available for the run.

The approved single stable policy is the system `performance` profile, with the CPU governor and EPP set to `performance` across CPU policies. The exact commands applied after approval were:

```bash
powerprofilesctl set performance
sudo cpupower frequency-set -g performance
```

The resulting state was verified: system and platform profiles `performance`; all 12 CPU policies use governor `performance` and EPP `performance`; minimum/maximum frequency limits remain unchanged. No fixed frequency, boost setting, or thermal/power limit was altered.

## Measurement setup

- Keep the existing C harness, pinned local OpenSSL 3.5.9 build, TLS 1.3 cipher, certificate, group, signature scheme, and client-side TCP_INFO instrumentation unchanged.
- Pin the client to CPU 2 and server to CPU 4. Confirm the topology and affinity immediately before collection.
- Run 10 warm-ups and 30 measured fresh handshakes per S0/S2/S3/S4 case. Randomize measured order with the new recorded seed.
- Create a new uniquely named immutable CSV and metadata JSON. Never modify or replace the Phase 2 CSV or metadata.
- The runner records environment snapshots before and after the batch: topology, per-CPU frequency and policy values, power profile, AC/battery state, load average, available thermal-zone readings, and top process names with lifetime CPU percentages. Missing sensors are recorded as unavailable; do not infer thermal or frequency values.
- Confirm AC is online and the approved policy is active immediately before starting. If power changes, AC disconnects, or severe background activity appears during the run, stop and preserve any partial output separately; do not call it a completed pilot.

## Reporting

Compare Phase 2B only for measurement stability, variance, outliers, and documented environmental changes. State clearly that this is diagnostic evidence and draw no performance conclusions. Do not start Phase 3.
