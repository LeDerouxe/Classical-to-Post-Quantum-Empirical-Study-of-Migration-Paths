#!/usr/bin/env python3
"""Reproducible, condition-specific analysis of one network-sensitivity campaign.

Raw observations and their metadata are read-only inputs. Derived tables are
written below data/processed/network, while the concise reviewed report is
written under docs/network-sensitivity.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = ROOT / "data" / "raw" / "network"
META_ROOT = ROOT / "data" / "metadata" / "network"
OUTPUT_ROOT = ROOT / "data" / "processed" / "network"
REPORT_PATH = ROOT / "docs" / "network-sensitivity" / "FINAL_NETWORK_ANALYSIS.md"
CASES = ("S0", "S2", "S3", "S4")
CONDITIONS = ("rtt-000ms", "rtt-001ms", "rtt-010ms", "rtt-050ms", "rtt-100ms")
EXPECTED = {
    "S0": ("x25519", "ecdsa_secp256r1_sha256"),
    "S2": ("X25519MLKEM768", "ecdsa_secp256r1_sha256"),
    "S3": ("X25519MLKEM768", "mldsa65"),
    "S4": ("MLKEM768", "mldsa65"),
}
BOOTSTRAP_ITERATIONS = 20_000
BOOTSTRAP_SEED = 2026111401


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q, method="linear"))


def iqr(values: np.ndarray) -> float:
    return percentile(values, 75) - percentile(values, 25)


def describe(values: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(values, dtype=float)
    median, mean = float(np.median(values)), float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return {
        "n": len(values), "median": median, "q1": percentile(values, 25),
        "q3": percentile(values, 75), "iqr": iqr(values), "mean": mean,
        "sd": sd, "cv_percent": 100 * sd / mean if mean else float("nan"),
        "p95": percentile(values, 95), "minimum": float(np.min(values)),
        "maximum": float(np.max(values)),
    }


def cluster_ci(frame: pd.DataFrame, case: str, metric: str, *, seed: int) -> tuple[float, float]:
    """Resample five condition-specific batches and rows within selected batches."""
    groups = [group[metric].to_numpy(float) for _, group in frame[frame.case_id == case].groupby("batch_id", sort=True)]
    data = np.stack(groups)
    rng = np.random.default_rng(seed)
    selected_batches = rng.integers(0, len(groups), size=(BOOTSTRAP_ITERATIONS, len(groups)))
    selected = data[selected_batches]
    selected_rows = rng.integers(0, data.shape[1], size=selected.shape)
    samples = np.take_along_axis(selected, selected_rows, axis=2).reshape(BOOTSTRAP_ITERATIONS, -1)
    medians = np.median(samples, axis=1)
    return percentile(medians, 2.5), percentile(medians, 97.5)


def contrast_ci(frame: pd.DataFrame, case: str, *, seed: int) -> tuple[float, float]:
    """Paired batch bootstrap CI for median(case) minus median(S0)."""
    if case == "S0":
        return 0.0, 0.0
    batches = sorted(frame.batch_id.unique())
    baseline = np.stack([frame[(frame.batch_id == batch) & (frame.case_id == "S0")]["tls_handshake_ms"].to_numpy(float) for batch in batches])
    candidate = np.stack([frame[(frame.batch_id == batch) & (frame.case_id == case)]["tls_handshake_ms"].to_numpy(float) for batch in batches])
    rng = np.random.default_rng(seed)
    selected = rng.integers(0, len(batches), size=(BOOTSTRAP_ITERATIONS, len(batches)))
    baseline_selected, candidate_selected = baseline[selected], candidate[selected]
    baseline_rows = rng.integers(0, baseline.shape[1], size=baseline_selected.shape)
    candidate_rows = rng.integers(0, candidate.shape[1], size=candidate_selected.shape)
    sampled_baseline = np.take_along_axis(baseline_selected, baseline_rows, axis=2).reshape(BOOTSTRAP_ITERATIONS, -1)
    sampled_candidate = np.take_along_axis(candidate_selected, candidate_rows, axis=2).reshape(BOOTSTRAP_ITERATIONS, -1)
    differences = np.median(sampled_candidate, axis=1) - np.median(sampled_baseline, axis=1)
    return percentile(differences, 2.5), percentile(differences, 97.5)


def markdown_table(frame: pd.DataFrame, decimals: int = 3) -> str:
    def render(value: object) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{value:.{decimals}f}"
        if isinstance(value, (int, np.integer)):
            return str(value)
        return str(value).replace("|", "\\|")
    rows = [[render(value) for value in row] for row in frame.itertuples(index=False, name=None)]
    headers = [str(column) for column in frame.columns]
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |", *["| " + " | ".join(row) + " |" for row in rows]])


def qdisc_ok(lines: list[str], delay: str) -> bool:
    netem = next((line for line in lines if "netem" in line), "")
    return bool(netem) and (delay == "0ms" or delay in netem)


def load(campaign: str) -> tuple[pd.DataFrame, dict, list[dict], list[Path]]:
    raw_dir, meta_dir = RAW_ROOT / campaign, META_ROOT / campaign
    csv_paths = sorted(raw_dir.glob("*.csv"))
    manifest_path = meta_dir / f"{campaign}.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(meta_dir.glob("*.json")) if path != manifest_path]
    return pd.concat([pd.read_csv(path) for path in csv_paths], ignore_index=True), manifest, metadata, csv_paths


def validate(frame: pd.DataFrame, manifest: dict, metadata: list[dict], csv_paths: list[Path]) -> list[str]:
    errors: list[str] = []
    if manifest.get("status") != "complete" or len(manifest.get("completed_batches", [])) != 25:
        errors.append("campaign manifest is not a complete 25-batch record")
    if len(csv_paths) != 25 or len(metadata) != 25 or len(frame) != 4000:
        errors.append("expected 25 CSVs, 25 batch metadata files, and 4,000 rows")
    if Counter(item["condition"]["condition_id"] for item in manifest.get("schedule", []) ) != Counter({condition: 5 for condition in CONDITIONS}):
        errors.append("campaign schedule does not contain five batches per condition")
    if len({item["collection_sequence"] for item in manifest.get("schedule", [])}) != 25:
        errors.append("collection schedule positions are not unique")
    if not (frame.handshake_success_failure == "success").all() or not (frame.client_returncode == 0).all() or not (frame.server_returncode == 0).all():
        errors.append("one or more handshakes or processes failed")
    if not (frame.tls_version == "TLSv1.3").all() or not (frame.cipher_suite == "TLS_AES_128_GCM_SHA256").all():
        errors.append("TLS version or cipher mismatch")
    for case, (group, signature) in EXPECTED.items():
        subset = frame[frame.case_id == case]
        if not (subset.observed_group.str.lower() == group.lower()).all() or not (subset.observed_signature_type.str.lower() == signature.lower()).all():
            errors.append(f"negotiation mismatch in {case}")
    counts = frame.groupby(["condition_id", "case_id", "warmup_flag"]).size()
    for condition in CONDITIONS:
        for case in CASES:
            if counts.get((condition, case, True), 0) != 50 or counts.get((condition, case, False), 0) != 150:
                errors.append(f"unexpected warm-up/measured count for {condition}/{case}")
    by_name = {path.name: path for path in csv_paths}
    for item in metadata:
        path = by_name.get(Path(item["csv_path"]).name)
        delay = item["condition"]["one_way_delay"]
        if item.get("status") != "completed" or path is None or sha256(path) != item.get("csv_sha256"):
            errors.append(f"metadata integrity mismatch in {item.get('batch_id')}")
        for snapshot in (item["environment_before"], item["environment_after"]):
            mains = any(power.get("type") == "Mains" and power.get("online") == "1" for power in snapshot["ac_battery"].values())
            policies = snapshot["cpu_policies"].values()
            if not mains or snapshot.get("power_profile") != "performance" or snapshot.get("platform_profile") != "performance" or any(p.get("scaling_governor") != "performance" or p.get("energy_performance_preference") != "performance" for p in policies):
                errors.append(f"environment guard mismatch in {item.get('batch_id')}")
        if not all(qdisc_ok(lines, delay) for lines in item["qdisc_before"].values()) or not all(qdisc_ok(lines, delay) for lines in item["qdisc_after"].values()):
            errors.append(f"qdisc guard mismatch in {item.get('batch_id')}")
    return errors


def write_report(campaign: str, frame: pd.DataFrame, integrity_errors: list[str], latency: pd.DataFrame, batch_consistency: pd.DataFrame, communication: pd.DataFrame) -> None:
    measured = frame[~frame.warmup_flag]
    lines = [
        "# Controlled Network-Sensitivity Analysis",
        "",
        "## Scope and inclusion rule",
        "",
        f"- Campaign: `{campaign}`.",
        "- This is a separate native Ubuntu namespace/veth/netem study. It neither replaces nor pools with the completed loopback or Windows campaigns.",
        "- The 1,000 protocol-defined warm-ups remain in raw data but are excluded from analysis. All 3,000 measured observations are retained; no statistical outlier is removed.",
        "- Each RTT condition is analyzed separately. The 0-ms condition is a namespace/veth topology control, not a duplicate of the primary loopback campaign.",
        "",
        "## Integrity gate",
        "",
        f"- Raw rows: {len(frame)}; warm-ups: {int(frame.warmup_flag.sum())}; measured rows: {len(measured)}.",
        f"- Validation errors: {'none' if not integrity_errors else '; '.join(integrity_errors)}.",
        "- All CIs below use 20,000 percentile bootstrap resamples that first resample the five batches of the stated RTT and then rows inside selected batches. With five batches, the intervals describe uncertainty and are not null-hypothesis tests.",
        "",
        "## TLS handshake duration by added RTT",
        "",
        "All values are milliseconds. `Contrast vs S0` is the condition-specific median(case) minus median(S0).",
        "",
        markdown_table(latency),
        "",
        "## Consistency across condition-specific batches",
        "",
        "For S2--S4, `positive batches` counts the five observed batches whose median contrast with S0 was above zero. The full batch table is retained as a derived CSV, rather than repeated here.",
        "",
        markdown_table(batch_consistency),
        "",
        "## Observed pattern",
        "",
        "At 10, 50, and 100 ms added RTT, S2 remains close to S0 in this harness, whereas S3 and S4 are about one added RTT above S0. That is an observation of these specific fresh TLS handshakes and their recorded packetization, not a general claim about all PQ TLS implementations or applications.",
        "",
        "## Communication and TCP-connect descriptors",
        "",
        "Bytes and packets are client-side TCP_INFO counters at SSL_connect completion. They do not include close packets or link/IP/TCP headers.",
        "",
        markdown_table(communication),
        "",
        "## Interpretation boundary",
        "",
        "The results characterize this one native Linux namespace/veth/netem case study with fixed symmetric delay, one OpenSSL build, fresh local processes, and local test credentials. They do not estimate browser behavior, public-PKI interoperability, Internet behavior, loss, congestion, bandwidth limitation, jitter, other hosts, or production workload effects.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True)
    args = parser.parse_args()
    frame, manifest, metadata, csv_paths = load(args.campaign)
    frame["warmup_flag"] = frame.warmup_flag.astype(str).str.lower().eq("true")
    for column in ("tls_handshake_ns", "tcp_connect_ns", "handshake_bytes", "packet_count", "client_returncode", "server_returncode"):
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["tls_handshake_ms"] = frame.tls_handshake_ns / 1_000_000
    frame["tcp_connect_ms"] = frame.tcp_connect_ns / 1_000_000
    errors = validate(frame, manifest, metadata, csv_paths)
    if errors:
        raise SystemExit("Integrity validation failed: " + "; ".join(errors))
    measured = frame[~frame.warmup_flag].copy()
    output = OUTPUT_ROOT / args.campaign
    output.mkdir(parents=True, exist_ok=True)
    measured.to_csv(output / "measured-observations.csv", index=False)
    latency_rows, contrast_rows, communication_rows, batch_rows = [], [], [], []
    for condition_index, condition in enumerate(CONDITIONS):
        subset = measured[measured.condition_id == condition]
        for case_index, case in enumerate(CASES):
            values = subset[subset.case_id == case].tls_handshake_ms.to_numpy(float)
            stats = describe(values)
            ci_low, ci_high = cluster_ci(subset, case, "tls_handshake_ms", seed=BOOTSTRAP_SEED + condition_index * 20 + case_index)
            baseline = subset[subset.case_id == "S0"].tls_handshake_ms.to_numpy(float)
            contrast_low, contrast_high = contrast_ci(subset, case, seed=BOOTSTRAP_SEED + 200 + condition_index * 20 + case_index)
            latency_rows.append({"condition": condition, "case": case, "n": stats["n"], "median_ms": stats["median"], "median_ci_low_ms": ci_low, "median_ci_high_ms": ci_high, "iqr_ms": stats["iqr"], "mean_ms": stats["mean"], "sd_ms": stats["sd"], "p95_ms_descriptive": stats["p95"], "min_ms": stats["minimum"], "max_ms": stats["maximum"], "contrast_vs_s0_ms": stats["median"] - float(np.median(baseline)), "contrast_ci_low_ms": contrast_low, "contrast_ci_high_ms": contrast_high})
            for batch_id, group in subset[subset.case_id == case].groupby("batch_id", sort=True):
                batch_rows.append({"condition": condition, "batch_id": batch_id, "case": case, "n": len(group), "median_ms": float(np.median(group.tls_handshake_ms)), "iqr_ms": iqr(group.tls_handshake_ms.to_numpy(float))})
            comm = {"condition": condition, "case": case, "n": len(values)}
            for label, column in (("handshake_bytes", "handshake_bytes"), ("packet_count", "packet_count"), ("tcp_connect_ms", "tcp_connect_ms")):
                metric = describe(subset[subset.case_id == case][column].to_numpy(float))
                comm[f"{label}_median"] = metric["median"]
                comm[f"{label}_iqr"] = metric["iqr"]
            communication_rows.append(comm)
        for batch_id, group in subset.groupby("batch_id", sort=True):
            baseline = float(np.median(group[group.case_id == "S0"].tls_handshake_ms))
            for case in CASES:
                case_median = float(np.median(group[group.case_id == case].tls_handshake_ms))
                contrast_rows.append({"condition": condition, "batch_id": batch_id, "case": case, "median_contrast_vs_s0_ms": case_median - baseline, "median_ratio_vs_s0": case_median / baseline})
    latency, contrasts = pd.DataFrame(latency_rows), pd.DataFrame(contrast_rows)
    communication, batches = pd.DataFrame(communication_rows), pd.DataFrame(batch_rows)
    batch_consistency = (contrasts.groupby(["condition", "case"], sort=False)
                         .agg(batches=("batch_id", "nunique"), positive_batches=("median_contrast_vs_s0_ms", lambda values: int((values > 0).sum())), min_batch_contrast_ms=("median_contrast_vs_s0_ms", "min"), max_batch_contrast_ms=("median_contrast_vs_s0_ms", "max"))
                         .reset_index())
    batch_consistency.loc[batch_consistency.case == "S0", "positive_batches"] = 0
    latency.to_csv(output / "latency-summary.csv", index=False)
    contrasts.to_csv(output / "batch-contrasts-vs-s0.csv", index=False)
    communication.to_csv(output / "communication-summary.csv", index=False)
    batches.to_csv(output / "batch-latency-summary.csv", index=False)
    batch_consistency.to_csv(output / "batch-contrast-consistency.csv", index=False)
    write_report(args.campaign, frame, errors, latency, batch_consistency, communication)
    print(json.dumps({"campaign": args.campaign, "raw_rows": len(frame), "measured_rows": len(measured), "processed_output": str(output.relative_to(ROOT)), "report": str(REPORT_PATH.relative_to(ROOT)), "bootstrap_iterations": BOOTSTRAP_ITERATIONS}, indent=2))


if __name__ == "__main__":
    main()
