#!/usr/bin/env python3
"""Reproducible, batch-aware analysis of one immutable final campaign.

The script never writes to raw data.  It creates derived CSV tables and a
Markdown report under data/processed/final/<campaign-id>/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = ROOT / "data" / "raw" / "final"
META_ROOT = ROOT / "data" / "metadata" / "final"
OUTPUT_ROOT = ROOT / "data" / "processed" / "final"
CASES = ("S0", "S2", "S3", "S4")
PRIMARY_METRIC = "tls_handshake_ms"
BOOTSTRAP_ITERATIONS = 20_000
BOOTSTRAP_SEED = 2026102001


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q, method="linear"))


def iqr(values: np.ndarray) -> float:
    return percentile(values, 75) - percentile(values, 25)


def summary(values: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(values, dtype=float)
    median = float(np.median(values))
    mean = float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    return {
        "n": len(values), "median": median, "q1": percentile(values, 25),
        "q3": percentile(values, 75), "iqr": iqr(values), "mean": mean,
        "sd": sd, "cv_percent": (100 * sd / mean) if mean else float("nan"),
        "p95": percentile(values, 95), "p99": percentile(values, 99),
        "minimum": float(np.min(values)), "maximum": float(np.max(values)),
    }


def outlier_count(values: np.ndarray) -> int:
    q1, q3 = percentile(values, 25), percentile(values, 75)
    fence = 1.5 * (q3 - q1)
    return int(np.sum((values < q1 - fence) | (values > q3 + fence)))


def cluster_bootstrap(
    frame: pd.DataFrame, metric: str, case: str, *, iterations: int, seed: int
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Percentile CIs for median and IQR, resampling batches then rows."""
    groups = [g[metric].to_numpy(float) for _, g in frame[frame.case_id == case].groupby("batch_id", sort=True)]
    rng = np.random.default_rng(seed)
    data = np.stack(groups)
    selected_batches = rng.integers(0, len(groups), size=(iterations, len(groups)))
    selected = data[selected_batches]
    selected_rows = rng.integers(0, data.shape[1], size=selected.shape)
    sample = np.take_along_axis(selected, selected_rows, axis=2).reshape(iterations, -1)
    medians = np.median(sample, axis=1)
    iqrs = np.percentile(sample, 75, axis=1, method="linear") - np.percentile(sample, 25, axis=1, method="linear")
    return (percentile(medians, 2.5), percentile(medians, 97.5)), (percentile(iqrs, 2.5), percentile(iqrs, 97.5))


def fixed_batch_bootstrap(
    frame: pd.DataFrame, metric: str, case: str, *, iterations: int, seed: int
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Sensitivity CI: resample rows within each observed batch, not batches."""
    groups = [g[metric].to_numpy(float) for _, g in frame[frame.case_id == case].groupby("batch_id", sort=True)]
    rng = np.random.default_rng(seed)
    data = np.stack(groups)
    selected_rows = rng.integers(0, data.shape[1], size=(iterations, *data.shape))
    sample = np.take_along_axis(data[None, :, :], selected_rows, axis=2).reshape(iterations, -1)
    medians = np.median(sample, axis=1)
    iqrs = np.percentile(sample, 75, axis=1, method="linear") - np.percentile(sample, 25, axis=1, method="linear")
    return (percentile(medians, 2.5), percentile(medians, 97.5)), (percentile(iqrs, 2.5), percentile(iqrs, 97.5))


def contrast_bootstrap(
    frame: pd.DataFrame, metric: str, numerator_case: str, denominator_case: str,
    *, iterations: int, seed: int
) -> tuple[float, float]:
    """Batch-paired percentile CI for median(numerator) minus denominator."""
    if numerator_case == denominator_case:
        return (0.0, 0.0)
    batch_ids = sorted(frame.batch_id.unique())
    baselines, candidates = [], []
    for batch_id in batch_ids:
        baseline = frame[(frame.batch_id == batch_id) & (frame.case_id == denominator_case)][metric].to_numpy(float)
        candidate = frame[(frame.batch_id == batch_id) & (frame.case_id == numerator_case)][metric].to_numpy(float)
        baselines.append(baseline)
        candidates.append(candidate)
    rng = np.random.default_rng(seed)
    baseline_data, candidate_data = np.stack(baselines), np.stack(candidates)
    selected_batches = rng.integers(0, len(batch_ids), size=(iterations, len(batch_ids)))
    baseline_selected, candidate_selected = baseline_data[selected_batches], candidate_data[selected_batches]
    baseline_rows = rng.integers(0, baseline_data.shape[1], size=baseline_selected.shape)
    candidate_rows = rng.integers(0, candidate_data.shape[1], size=candidate_selected.shape)
    sampled_baseline = np.take_along_axis(baseline_selected, baseline_rows, axis=2).reshape(iterations, -1)
    sampled_candidate = np.take_along_axis(candidate_selected, candidate_rows, axis=2).reshape(iterations, -1)
    differences = np.median(sampled_candidate, axis=1) - np.median(sampled_baseline, axis=1)
    return percentile(differences, 2.5), percentile(differences, 97.5)


def fixed_batch_contrast_bootstrap(
    frame: pd.DataFrame, metric: str, numerator_case: str, denominator_case: str,
    *, iterations: int, seed: int
) -> tuple[float, float]:
    """Sensitivity contrast CI retaining the five observed batches."""
    if numerator_case == denominator_case:
        return (0.0, 0.0)
    batch_ids = sorted(frame.batch_id.unique())
    baseline = np.stack([
        frame[(frame.batch_id == batch_id) & (frame.case_id == denominator_case)][metric].to_numpy(float)
        for batch_id in batch_ids
    ])
    candidate = np.stack([
        frame[(frame.batch_id == batch_id) & (frame.case_id == numerator_case)][metric].to_numpy(float)
        for batch_id in batch_ids
    ])
    rng = np.random.default_rng(seed)
    baseline_rows = rng.integers(0, baseline.shape[1], size=(iterations, *baseline.shape))
    candidate_rows = rng.integers(0, candidate.shape[1], size=(iterations, *candidate.shape))
    sampled_baseline = np.take_along_axis(baseline[None, :, :], baseline_rows, axis=2).reshape(iterations, -1)
    sampled_candidate = np.take_along_axis(candidate[None, :, :], candidate_rows, axis=2).reshape(iterations, -1)
    differences = np.median(sampled_candidate, axis=1) - np.median(sampled_baseline, axis=1)
    return percentile(differences, 2.5), percentile(differences, 97.5)


def load_campaign(campaign_id: str) -> tuple[pd.DataFrame, list[dict], list[Path]]:
    raw_dir = RAW_ROOT / campaign_id
    metadata_dir = META_ROOT / campaign_id
    csv_paths = sorted(raw_dir.glob("*.csv"))
    metadata_paths = sorted(metadata_dir.glob("*.json"))
    if len(csv_paths) != 5 or len(metadata_paths) != 5:
        raise SystemExit("Expected exactly five CSVs and five metadata files for the completed campaign.")
    frames = [pd.read_csv(path) for path in csv_paths]
    records = [json.loads(path.read_text()) for path in metadata_paths]
    return pd.concat(frames, ignore_index=True), records, csv_paths


def validate(frame: pd.DataFrame, metadata: list[dict], csv_paths: list[Path]) -> list[str]:
    errors = []
    required = {
        "batch_id", "case_id", "sequence_index", "warmup_flag", "tls_version", "cipher_suite",
        "requested_group", "observed_group", "requested_signature_type", "observed_signature_type",
        "handshake_success_failure", "tls_handshake_ns", "handshake_bytes", "packet_count",
    }
    missing = required - set(frame.columns)
    if missing:
        errors.append(f"missing columns: {sorted(missing)}")
    if len(frame) != 800:
        errors.append(f"expected 800 rows, observed {len(frame)}")
    if frame.batch_id.nunique() != 5:
        errors.append(f"expected five batches, observed {frame.batch_id.nunique()}")
    if not (frame.handshake_success_failure == "success").all():
        errors.append("not all handshakes succeeded")
    if not (frame.tls_version == "TLSv1.3").all() or not (frame.cipher_suite == "TLS_AES_128_GCM_SHA256").all():
        errors.append("TLS version or cipher mismatch")
    if not (frame.requested_group.str.lower() == frame.observed_group.str.lower()).all():
        errors.append("negotiated group mismatch")
    if not (frame.requested_signature_type.str.lower() == frame.observed_signature_type.str.lower()).all():
        errors.append("negotiated signature mismatch")
    if (frame.handshake_bytes <= 0).any() or (frame.packet_count <= 0).any():
        errors.append("non-positive TCP_INFO counter")
    measured = frame[~frame.warmup_flag]
    for case in CASES:
        if len(measured[measured.case_id == case]) != 150:
            errors.append(f"{case} does not have 150 measured observations")
    expected_hashes = {item["csv_path"].split("/")[-1]: item.get("csv_sha256") for item in metadata}
    for path in csv_paths:
        if sha256(path) != expected_hashes.get(path.name):
            errors.append(f"checksum mismatch: {path.name}")
    if not all(item.get("status") == "completed" for item in metadata):
        errors.append("one or more metadata records are not completed")
    return errors


def environmental_table(metadata: list[dict]) -> pd.DataFrame:
    rows = []
    for item in sorted(metadata, key=lambda value: value["batch_number"]):
        before, after = item["environment_before"], item["environment_after"]
        def package(snapshot: dict) -> float | None:
            zones = snapshot.get("thermal_zones", {})
            for zone in zones.values():
                if zone.get("type") == "x86_pkg_temp":
                    return zone.get("temp_c")
            return None
        rows.append({
            "batch_id": item["batch_id"], "batch_number": item["batch_number"],
            "status": item["status"], "start_utc": item["batch_start_utc"], "end_utc": item["batch_end_utc"],
            "load_1m_before": before.get("load_average_1_5_15m", [None])[0],
            "load_1m_after": after.get("load_average_1_5_15m", [None])[0],
            "package_temp_c_before": package(before), "package_temp_c_after": package(after),
            "ac_before": any(v.get("online") == "1" for v in before.get("ac_battery", {}).values()),
            "ac_after": any(v.get("online") == "1" for v in after.get("ac_battery", {}).values()),
            "power_profile_before": before.get("power_profile"), "power_profile_after": after.get("power_profile"),
            "platform_profile_before": before.get("platform_profile"), "platform_profile_after": after.get("platform_profile"),
        })
    return pd.DataFrame(rows)


def markdown_table(frame: pd.DataFrame, decimals: int = 3) -> str:
    """Small dependency-free Markdown renderer for derived report tables."""
    headers = [str(column) for column in frame.columns]
    def format_value(value: object) -> str:
        if isinstance(value, (float, np.floating)):
            return f"{value:.{decimals}f}"
        if isinstance(value, (int, np.integer)):
            return str(value)
        return str(value).replace("|", "\\|")
    rows = [[format_value(value) for value in row] for row in frame.itertuples(index=False, name=None)]
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *["| " + " | ".join(row) + " |" for row in rows],
    ])


def write_report(output: Path, campaign_id: str, frame: pd.DataFrame, environment: pd.DataFrame,
                 latency: pd.DataFrame, resources: pd.DataFrame, communication: pd.DataFrame,
                 batch_latency: pd.DataFrame, batch_contrasts: pd.DataFrame,
                 validation_errors: list[str]) -> None:
    measured = frame[~frame.warmup_flag]
    lines = [
        "# Final Ubuntu Campaign Analysis",
        "",
        "## Scope and analysis rules",
        "",
        f"- Campaign: `{campaign_id}`.",
        "- Raw data are immutable. This report uses only rows flagged as measured; the 200 protocol-defined warm-ups are retained in raw files but excluded from inference.",
        "- No observation is removed for being statistically unusual. Outlier counts are descriptive only.",
        f"- Primary endpoint: client `SSL_connect()` duration (`tls_handshake_ms`). The primary CIs use {BOOTSTRAP_ITERATIONS:,} percentile bootstrap resamples that first resample the five batches and then resample observations inside selected batches.",
        "- A fixed-batch bootstrap sensitivity CI is also reported. It resamples observations within the five observed batches while retaining their membership, so it does not generalize over batches.",
        "- With five batches, bootstrap intervals are uncertainty descriptions, not a basis for null-hypothesis claims. Batch-level tables are reported alongside pooled results.",
        "",
        "## Data-integrity gate",
        "",
        f"- Raw rows: {len(frame)}; warm-ups: {int(frame.warmup_flag.sum())}; measured rows: {len(measured)}.",
        f"- Handshake successes: {int((frame.handshake_success_failure == 'success').sum())}/{len(frame)}.",
        f"- Validation errors: {'none' if not validation_errors else '; '.join(validation_errors)}.",
        "",
        "## Primary latency summary",
        "",
        "All units are milliseconds. `S0 contrast` is median(case) minus median(S0); the CI is batch-paired and cluster-bootstrap based.",
        "",
        markdown_table(latency),
        "",
        "## Per-batch latency medians",
        "",
        "These values expose batch-to-batch behavior without treating the 600 rows as one homogeneous stream.",
        "",
        markdown_table(batch_latency),
        "",
        "## Batch-paired contrasts with S0",
        "",
        "Every batch-specific contrast is reported below. The consistency of direction across batches is more informative here than a p-value, given five batches.",
        "",
        markdown_table(batch_contrasts),
        "",
        "## Resource metrics",
        "",
        "CPU time is the sum of user and system time within each role's defined timing boundary. Peak RSS is per fresh process; it is a process-level maximum, not total system memory.",
        "",
        markdown_table(resources),
        "",
        "## Communication metrics",
        "",
        "Bytes and packet counts are the validated client-side TCP_INFO values at the SSL_connect completion boundary. They exclude close packets and do not include network headers.",
        "",
        markdown_table(communication),
        "",
        "## Batch environment snapshots",
        "",
        markdown_table(environment),
        "",
        "## Interpretation boundary",
        "",
        "This report describes one native Ubuntu loopback TLS 1.3/OpenSSL case study. It does not establish results for external networks, other OpenSSL versions, other hardware, Windows, or production application workloads. Cross-platform and controlled-network phases remain separate work.",
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True, help="Campaign directory name under data/raw/final")
    args = parser.parse_args()
    frame, metadata, csv_paths = load_campaign(args.campaign)
    frame["warmup_flag"] = frame["warmup_flag"].astype(str).str.lower().eq("true")
    numeric = ["tls_handshake_ns", "tcp_connect_ns", "client_user_cpu_ns", "client_system_cpu_ns",
               "server_user_cpu_ns", "server_system_cpu_ns", "client_peak_rss_kib", "server_peak_rss_kib",
               "handshake_bytes", "packet_count"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    frame["tls_handshake_ms"] = frame.tls_handshake_ns / 1_000_000
    frame["tcp_connect_ms"] = frame.tcp_connect_ns / 1_000_000
    frame["client_cpu_ms"] = (frame.client_user_cpu_ns + frame.client_system_cpu_ns) / 1_000_000
    frame["server_cpu_ms"] = (frame.server_user_cpu_ns + frame.server_system_cpu_ns) / 1_000_000
    validation_errors = validate(frame, metadata, csv_paths)
    if validation_errors:
        raise SystemExit("Integrity validation failed: " + "; ".join(validation_errors))
    measured = frame[~frame.warmup_flag].copy()
    output = OUTPUT_ROOT / args.campaign
    output.mkdir(parents=True, exist_ok=True)
    measured.to_csv(output / "measured-observations.csv", index=False)
    environment = environmental_table(metadata)
    environment.to_csv(output / "batch-environment.csv", index=False)

    latency_rows, batch_rows, batch_contrast_rows, resource_rows, communication_rows = [], [], [], [], []
    for index, case in enumerate(CASES):
        values = measured[measured.case_id == case][PRIMARY_METRIC].to_numpy(float)
        stats = summary(values)
        median_ci, iqr_ci = cluster_bootstrap(measured, PRIMARY_METRIC, case,
                                              iterations=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED + index)
        fixed_median_ci, fixed_iqr_ci = fixed_batch_bootstrap(
            measured, PRIMARY_METRIC, case,
            iterations=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED + 50 + index,
        )
        baseline_median = float(np.median(measured[measured.case_id == "S0"][PRIMARY_METRIC]))
        contrast_ci = contrast_bootstrap(
            measured, PRIMARY_METRIC, case, "S0",
            iterations=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED + 100 + index,
        )
        fixed_contrast_ci = fixed_batch_contrast_bootstrap(
            measured, PRIMARY_METRIC, case, "S0",
            iterations=BOOTSTRAP_ITERATIONS, seed=BOOTSTRAP_SEED + 150 + index,
        )
        latency_rows.append({
            "case": case, "n": stats["n"], "median_ms": stats["median"],
            "median_ci_low_ms": median_ci[0], "median_ci_high_ms": median_ci[1],
            "median_ci_fixed_batches_low_ms": fixed_median_ci[0], "median_ci_fixed_batches_high_ms": fixed_median_ci[1],
            "iqr_ms": stats["iqr"], "iqr_ci_low_ms": iqr_ci[0], "iqr_ci_high_ms": iqr_ci[1],
            "iqr_ci_fixed_batches_low_ms": fixed_iqr_ci[0], "iqr_ci_fixed_batches_high_ms": fixed_iqr_ci[1],
            "mean_ms": stats["mean"], "sd_ms": stats["sd"], "cv_percent": stats["cv_percent"],
            "p95_ms_descriptive": stats["p95"], "p99_ms_descriptive": stats["p99"],
            "min_ms": stats["minimum"], "max_ms": stats["maximum"],
            "outliers_1_5_iqr": outlier_count(values), "s0_median_contrast_ms": stats["median"] - baseline_median,
            "s0_contrast_ci_low_ms": contrast_ci[0], "s0_contrast_ci_high_ms": contrast_ci[1],
            "s0_contrast_ci_fixed_batches_low_ms": fixed_contrast_ci[0],
            "s0_contrast_ci_fixed_batches_high_ms": fixed_contrast_ci[1],
        })
        for batch_id, group in measured[measured.case_id == case].groupby("batch_id", sort=True):
            batch_values = group[PRIMARY_METRIC].to_numpy(float)
            batch_rows.append({"batch_id": batch_id, "case": case, "n": len(batch_values),
                               "median_ms": float(np.median(batch_values)), "iqr_ms": iqr(batch_values),
                               "minimum_ms": float(np.min(batch_values)), "maximum_ms": float(np.max(batch_values))})
            baseline_values = measured[(measured.batch_id == batch_id) & (measured.case_id == "S0")][PRIMARY_METRIC].to_numpy(float)
            batch_contrast_rows.append({
                "batch_id": batch_id, "case": case, "median_contrast_vs_s0_ms": float(np.median(batch_values) - np.median(baseline_values)),
                "median_ratio_vs_s0": float(np.median(batch_values) / np.median(baseline_values)),
            })
        resource = {"case": case, "n": len(values)}
        for name, column in (("client_cpu_ms", "client_cpu_ms"), ("server_cpu_ms", "server_cpu_ms"),
                             ("client_peak_rss_kib", "client_peak_rss_kib"), ("server_peak_rss_kib", "server_peak_rss_kib")):
            metric = summary(measured[measured.case_id == case][column].to_numpy(float))
            resource[f"{name}_median"] = metric["median"]
            resource[f"{name}_iqr"] = metric["iqr"]
        resource_rows.append(resource)
        communication = {"case": case, "n": len(values)}
        for name in ("handshake_bytes", "packet_count", "tcp_connect_ms"):
            metric = summary(measured[measured.case_id == case][name].to_numpy(float))
            communication[f"{name}_median"] = metric["median"]
            communication[f"{name}_iqr"] = metric["iqr"]
            communication[f"{name}_min"] = metric["minimum"]
            communication[f"{name}_max"] = metric["maximum"]
        communication_rows.append(communication)
    latency = pd.DataFrame(latency_rows)
    batch_latency = pd.DataFrame(batch_rows)
    batch_contrasts = pd.DataFrame(batch_contrast_rows)
    resources = pd.DataFrame(resource_rows)
    communication = pd.DataFrame(communication_rows)
    latency.to_csv(output / "latency-summary.csv", index=False)
    batch_latency.to_csv(output / "batch-latency-summary.csv", index=False)
    batch_contrasts.to_csv(output / "batch-latency-contrasts-vs-s0.csv", index=False)
    resources.to_csv(output / "resource-summary.csv", index=False)
    communication.to_csv(output / "communication-summary.csv", index=False)
    write_report(output / "analysis-report.md", args.campaign, frame, environment, latency, resources,
                 communication, batch_latency, batch_contrasts, validation_errors)
    print(json.dumps({"campaign": args.campaign, "output": str(output.relative_to(ROOT)),
                      "rows": len(frame), "measured_rows": len(measured), "bootstrap_iterations": BOOTSTRAP_ITERATIONS}, indent=2))


if __name__ == "__main__":
    main()
