#!/usr/bin/env python3
"""Reproducible analysis of one immutable Windows validation campaign.

The script writes derived outputs only. It validates raw CSV checksums against
the campaign metadata and never changes raw observations or metadata.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = ROOT / "data" / "raw" / "windows"
META_ROOT = ROOT / "data" / "metadata" / "windows"
OUTPUT_ROOT = ROOT / "data" / "processed" / "windows"
CASES = ("S0", "S2", "S3", "S4")
ITERATIONS = 20_000
SEED = 2026110901


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: np.ndarray, q: float) -> float:
    return float(np.percentile(values, q, method="linear"))


def iqr(values: np.ndarray) -> float:
    return percentile(values, 75) - percentile(values, 25)


def summary(values: np.ndarray) -> dict[str, float | int]:
    values = np.asarray(values, dtype=float)
    median, mean = float(np.median(values)), float(np.mean(values))
    sd = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
    q1, q3 = percentile(values, 25), percentile(values, 75)
    fence = 1.5 * (q3 - q1)
    return {
        "n": len(values), "median": median, "q1": q1, "q3": q3,
        "iqr": q3 - q1, "mean": mean, "sd": sd,
        "cv_percent": 100 * sd / mean if mean else float("nan"),
        "p95": percentile(values, 95), "p99": percentile(values, 99),
        "minimum": float(np.min(values)), "maximum": float(np.max(values)),
        "outliers_1_5_iqr": int(np.sum((values < q1 - fence) | (values > q3 + fence))),
    }


def case_matrix(frame: pd.DataFrame, case: str) -> np.ndarray:
    groups = [group.latency_ms.to_numpy(float) for _, group in frame[frame.case_id == case].groupby("batch_id", sort=True)]
    if len(groups) != 5 or len({len(group) for group in groups}) != 1:
        raise ValueError(f"unexpected batch structure for {case}")
    return np.stack(groups)


def cluster_ci(frame: pd.DataFrame, case: str, seed: int) -> tuple[tuple[float, float], tuple[float, float]]:
    data, rng = case_matrix(frame, case), np.random.default_rng(seed)
    selected_batches = rng.integers(0, data.shape[0], size=(ITERATIONS, data.shape[0]))
    selected = data[selected_batches]
    selected_rows = rng.integers(0, data.shape[1], size=selected.shape)
    samples = np.take_along_axis(selected, selected_rows, axis=2).reshape(ITERATIONS, -1)
    medians = np.median(samples, axis=1)
    iqrs = np.percentile(samples, 75, axis=1, method="linear") - np.percentile(samples, 25, axis=1, method="linear")
    return (percentile(medians, 2.5), percentile(medians, 97.5)), (percentile(iqrs, 2.5), percentile(iqrs, 97.5))


def contrast_ci(frame: pd.DataFrame, case: str, seed: int) -> tuple[float, float]:
    if case == "S0":
        return 0.0, 0.0
    baseline, candidate = case_matrix(frame, "S0"), case_matrix(frame, case)
    rng = np.random.default_rng(seed)
    batches = rng.integers(0, baseline.shape[0], size=(ITERATIONS, baseline.shape[0]))
    baseline_selected, candidate_selected = baseline[batches], candidate[batches]
    baseline_rows = rng.integers(0, baseline.shape[1], size=baseline_selected.shape)
    candidate_rows = rng.integers(0, candidate.shape[1], size=candidate_selected.shape)
    baseline_sample = np.take_along_axis(baseline_selected, baseline_rows, axis=2).reshape(ITERATIONS, -1)
    candidate_sample = np.take_along_axis(candidate_selected, candidate_rows, axis=2).reshape(ITERATIONS, -1)
    contrasts = np.median(candidate_sample, axis=1) - np.median(baseline_sample, axis=1)
    return percentile(contrasts, 2.5), percentile(contrasts, 97.5)


def markdown(frame: pd.DataFrame, decimals: int = 3) -> str:
    headers = [str(column) for column in frame.columns]
    def value(item: object) -> str:
        if isinstance(item, (float, np.floating)):
            return f"{item:.{decimals}f}"
        if isinstance(item, (int, np.integer)):
            return str(item)
        return str(item).replace("|", "\\|")
    rows = [[value(item) for item in row] for row in frame.itertuples(index=False, name=None)]
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |", *["| " + " | ".join(row) + " |" for row in rows]])


def load(campaign: str) -> tuple[pd.DataFrame, dict, list[Path]]:
    raw_dir, metadata_dir = RAW_ROOT / campaign, META_ROOT / campaign
    csv_paths = sorted(raw_dir.glob("*.csv"))
    metadata_paths = sorted(metadata_dir.glob(f"{campaign}.json"))
    if len(csv_paths) != 5 or len(metadata_paths) != 1:
        raise SystemExit("expected exactly five CSVs and one completed campaign metadata file")
    return pd.concat([pd.read_csv(path) for path in csv_paths], ignore_index=True), json.loads(metadata_paths[0].read_text()), csv_paths


def validate(frame: pd.DataFrame, metadata: dict, csv_paths: list[Path]) -> list[str]:
    errors = []
    required = {"batch_id", "case_id", "warmup_flag", "latency_ns", "client_returncode", "server_returncode", "validation_ok", "tls_version", "cipher_suite", "observed_group", "peer_public_key_type", "certificate_verify_signature_scheme", "chain_result", "hostname_result", "client_affinity_mask", "server_affinity_mask"}
    missing = required - set(frame.columns)
    if missing:
        errors.append(f"missing columns: {sorted(missing)}")
    if len(frame) != 800 or frame.batch_id.nunique() != 5:
        errors.append(f"unexpected row or batch count: rows={len(frame)}, batches={frame.batch_id.nunique()}")
    if metadata.get("status") != "complete" or len(metadata.get("batches", [])) != 5:
        errors.append("campaign metadata does not record five completed batches")
    hashes = {Path(item["csv"]).name: item["sha256"] for item in metadata.get("batches", [])}
    for path in csv_paths:
        if sha256(path) != hashes.get(path.name):
            errors.append(f"checksum mismatch: {path.name}")
    if not (frame.client_returncode == 0).all() or not (frame.server_returncode == 0).all() or not (frame.validation_ok.astype(str).str.lower() == "true").all():
        errors.append("one or more handshake results failed")
    if not (frame.tls_version == "TLSv1.3").all() or not (frame.cipher_suite == "TLS_AES_128_GCM_SHA256").all():
        errors.append("TLS version or cipher mismatch")
    if not (frame.chain_result == "PASS").all() or not (frame.hostname_result == "PASS").all():
        errors.append("certificate-chain or hostname verification failed")
    expected = {
        "S0": ("x25519", "EC", "ecdsa_secp256r1_sha256"),
        "S2": ("X25519MLKEM768", "EC", "ecdsa_secp256r1_sha256"),
        "S3": ("X25519MLKEM768", "ML-DSA-65", "mldsa65"),
        "S4": ("MLKEM768", "ML-DSA-65", "mldsa65"),
    }
    for case, (group, key_type, signature) in expected.items():
        subset = frame[frame.case_id == case]
        if not (subset.observed_group.str.lower() == group.lower()).all() or not (subset.server_group.str.lower() == group.lower()).all():
            errors.append(f"negotiated group mismatch for {case}")
        if not (subset.peer_public_key_type == key_type).all() or not (subset.certificate_verify_signature_scheme.str.lower() == signature.lower()).all() or not (subset.server_signature.str.lower() == signature.lower()).all():
            errors.append(f"authentication mismatch for {case}")
    measured = frame[~frame.warmup_flag]
    for case in CASES:
        if len(measured[measured.case_id == case]) != 150:
            errors.append(f"{case} does not have 150 measured observations")
    return errors


def write_report(path: Path, campaign: str, raw: pd.DataFrame, latency: pd.DataFrame,
                 batch: pd.DataFrame, environment: pd.DataFrame, errors: list[str]) -> None:
    measured = raw[~raw.warmup_flag]
    path.write_text("\n".join([
        "# Final Windows Validation Analysis", "",
        "## Scope and analysis rules", "",
        f"- Campaign: `{campaign}`.",
        "- This is a separate Windows 11 validation on the same physical Intel Core i5-12450H used for the Ubuntu primary campaign. Windows and Ubuntu observations are not pooled.",
        "- The endpoint is the QueryPerformanceCounter interval immediately around client `SSL_connect()`. The 200 retained warm-ups are excluded from inference; no measured observation is removed.",
        f"- Each reported 95% CI is a {ITERATIONS:,}-resample percentile bootstrap that resamples the five batches and then observations inside selected batches. With five batches, it is an uncertainty description, not a null-hypothesis test.",
        "- The Windows result supports only a qualitative check of the direction of within-platform S0 contrasts. It does not estimate a Windows-minus-Ubuntu absolute-time effect.", "",
        "## Data-integrity gate", "",
        f"- Raw rows: {len(raw)}; warm-ups: {int(raw.warmup_flag.sum())}; measured rows: {len(measured)}.",
        f"- All client/server return codes and configuration validations passed: {int(raw.validation_ok.sum())}/{len(raw)} rows.",
        f"- Validation errors: {'none' if not errors else '; '.join(errors)}.", "",
        "## Latency summary", "",
        "All units are milliseconds. `S0 contrast` is median(case) minus median(S0).", "",
        markdown(latency), "",
        "## Per-batch latency and direction", "",
        "Each case has 30 measured handshakes per batch. `contrast_vs_S0_ms` is calculated from medians within the same batch.", "",
        markdown(batch), "",
        "## Environment snapshots", "",
        "AC and the selected `High performance` scheme were recorded before and after every batch. The detailed processor-set topology and affinity masks are retained in the campaign metadata.", "",
        markdown(environment), "",
        "## Interpretation boundary", "",
        "This report concerns one device, one Windows 11 build, one OpenSSL build, loopback transport, and local credentials. It provides neither browser/public-PKI interoperability evidence nor an external-network or general operating-system performance result.", "",
    ]), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign", required=True)
    args = parser.parse_args()
    raw, metadata, paths = load(args.campaign)
    raw["warmup_flag"] = raw.warmup_flag.astype(str).str.lower().eq("true")
    raw["latency_ns"] = pd.to_numeric(raw.latency_ns, errors="raise")
    raw["latency_ms"] = raw.latency_ns / 1_000_000
    errors = validate(raw, metadata, paths)
    if errors:
        raise SystemExit("integrity validation failed: " + "; ".join(errors))
    measured = raw[~raw.warmup_flag].copy()
    summary_rows, batch_rows = [], []
    baseline_median = float(np.median(measured[measured.case_id == "S0"].latency_ms))
    for index, case in enumerate(CASES):
        values = measured[measured.case_id == case].latency_ms.to_numpy(float)
        stats = summary(values)
        median_ci, iqr_ci = cluster_ci(measured, case, SEED + index)
        contrast_interval = contrast_ci(measured, case, SEED + 100 + index)
        summary_rows.append({"case": case, "n": stats["n"], "median_ms": stats["median"], "median_ci_low_ms": median_ci[0], "median_ci_high_ms": median_ci[1], "iqr_ms": stats["iqr"], "iqr_ci_low_ms": iqr_ci[0], "iqr_ci_high_ms": iqr_ci[1], "mean_ms_descriptive": stats["mean"], "sd_ms_descriptive": stats["sd"], "cv_percent_descriptive": stats["cv_percent"], "p95_ms_descriptive": stats["p95"], "p99_ms_descriptive": stats["p99"], "min_ms": stats["minimum"], "max_ms": stats["maximum"], "outliers_1_5_iqr_descriptive": stats["outliers_1_5_iqr"], "s0_median_contrast_ms": stats["median"] - baseline_median, "s0_contrast_ci_low_ms": contrast_interval[0], "s0_contrast_ci_high_ms": contrast_interval[1]})
        for batch_id, group in measured[measured.case_id == case].groupby("batch_id", sort=True):
            value = group.latency_ms.to_numpy(float)
            s0 = measured[(measured.batch_id == batch_id) & (measured.case_id == "S0")].latency_ms.to_numpy(float)
            batch_rows.append({"batch_id": batch_id, "case": case, "n": len(value), "median_ms": float(np.median(value)), "iqr_ms": iqr(value), "contrast_vs_s0_ms": float(np.median(value) - np.median(s0)), "ratio_vs_s0": float(np.median(value) / np.median(s0))})
    summary_frame, batch_frame = pd.DataFrame(summary_rows), pd.DataFrame(batch_rows)
    environment = pd.DataFrame([{"batch_id": item["batch_id"], "ac_before": item["environment_before"]["power"]["ac_line_status"], "ac_after": item["environment_after"]["power"]["ac_line_status"], "scheme_before": item["environment_before"]["active_power_scheme"]["name"], "scheme_after": item["environment_after"]["active_power_scheme"]["name"]} for item in metadata["batches"]])
    output = OUTPUT_ROOT / args.campaign
    output.mkdir(parents=True, exist_ok=True)
    measured.to_csv(output / "measured-observations.csv", index=False)
    summary_frame.to_csv(output / "latency-summary.csv", index=False)
    batch_frame.to_csv(output / "batch-latency-summary.csv", index=False)
    environment.to_csv(output / "batch-environment.csv", index=False)
    write_report(output / "analysis-report.md", args.campaign, raw, summary_frame, batch_frame, environment, errors)
    print(json.dumps({"campaign": args.campaign, "output": str(output.relative_to(ROOT)), "measured_rows": len(measured), "bootstrap_iterations": ITERATIONS}, indent=2))


if __name__ == "__main__":
    main()
