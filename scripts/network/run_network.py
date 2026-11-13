#!/usr/bin/env python3
"""Guarded, immutable Linux namespace/veth/netem network-sensitivity study."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import random
import re
import select
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/network/network.json"
OPENSSL_DIR = ROOT / "third_party/openssl-3.5.9/install"
OPENSSL_BIN = OPENSSL_DIR / "bin/openssl"
OPENSSL_SOURCE = OPENSSL_DIR.parent / "source"
HARNESS_SOURCE = ROOT / "scripts/network/tls_network.c"
BUILD_DIR = ROOT / "build/network"
RAW_ROOT = ROOT / "data/raw/network"
META_ROOT = ROOT / "data/metadata/network"
EVIDENCE_ROOT = ROOT / "evidence/network-workflow"
CLIENT_VETH, SERVER_VETH = "veth-pqc-client", "veth-pqc-server"
FIELDS = ["condition_id", "batch_id", "run_id", "timestamp", "case_id", "sequence_index", "warmup_flag", "git_commit_hash", "openssl_version", "openssl_source_commit", "tls_version", "cipher_suite", "requested_group", "observed_group", "requested_signature_type", "observed_signature_type", "handshake_success_failure", "tcp_connect_ns", "tls_handshake_ns", "handshake_bytes", "packet_count", "client_returncode", "server_returncode", "error_reason"]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(cmd: list[str], *, env: dict[str, str] | None = None, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=timeout, check=False)


def checked(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    result = command(cmd, **kwargs)
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {' '.join(map(str, cmd))}\n{result.stderr[-1200:]}")
    return result


def local_env() -> dict[str, str]:
    result = os.environ.copy()
    result["LD_LIBRARY_PATH"] = str(OPENSSL_DIR / "lib")
    result["OPENSSL_CONF"] = str(ROOT / "configs/openssl/feasibility-openssl.cnf")
    return result


def namespace_command(namespace: str, args: list[str]) -> list[str]:
    return ["sudo", "-n", "ip", "netns", "exec", namespace, "env", f"LD_LIBRARY_PATH={OPENSSL_DIR / 'lib'}", f"OPENSSL_CONF={ROOT / 'configs/openssl/feasibility-openssl.cnf'}", *args]


def load_final_helpers():
    spec = importlib.util.spec_from_file_location("network_final_helpers", ROOT / "scripts/final/run_final.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load reviewed final-workflow helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_commit() -> str:
    return checked(["git", "rev-parse", "HEAD"]).stdout.strip()


def qdisc_snapshot(cfg: dict) -> dict[str, list[str]]:
    return {
        namespace: checked(["sudo", "-n", "ip", "netns", "exec", namespace, "tc", "-s", "qdisc", "show", "dev", device]).stdout.splitlines()
        for namespace, device in ((cfg["client_namespace"], CLIENT_VETH), (cfg["server_namespace"], SERVER_VETH))
    }


def topology_snapshot(cfg: dict) -> dict[str, dict[str, str]]:
    result = {}
    for namespace, device, address in ((cfg["client_namespace"], CLIENT_VETH, cfg["client_address"]), (cfg["server_namespace"], SERVER_VETH, cfg["server_address"])):
        output = checked(["sudo", "-n", "ip", "netns", "exec", namespace, "ip", "-brief", "addr", "show", "dev", device]).stdout.strip()
        link = checked(["sudo", "-n", "ip", "netns", "exec", namespace, "ip", "-o", "link", "show", "dev", device]).stdout.strip()
        if address not in output or "UP" not in output or "mtu 1500" not in link:
            raise RuntimeError(f"namespace topology check failed for {namespace}: {output!r}")
        result[namespace] = {"address": output, "link": link}
    return result


def set_delay(cfg: dict, condition: dict) -> None:
    for namespace, device in ((cfg["client_namespace"], CLIENT_VETH), (cfg["server_namespace"], SERVER_VETH)):
        checked(["sudo", "-n", "ip", "netns", "exec", namespace, "tc", "qdisc", "replace", "dev", device, "root", "netem", "limit", "1000", "delay", condition["one_way_delay"]])


def qdisc_errors(condition: dict, snapshot: dict[str, list[str]]) -> list[str]:
    raw = condition["one_way_delay"]
    expected_us = float(raw[:-2]) * (1000 if raw.endswith("ms") else 1)
    failures = []
    for namespace, lines in snapshot.items():
        netem = next((line for line in lines if "netem" in line), "")
        match = re.search(r"delay\s+([0-9.]+)(us|ms)", netem)
        if not match:
            # tc omits the delay attribute when a netem qdisc is configured
            # with a zero delay. Its presence is sufficient for the 0-ms
            # topology-control condition; every nonzero condition must show
            # its configured delay explicitly.
            if not netem or expected_us != 0:
                failures.append(namespace)
            continue
        actual_us = float(match.group(1)) * (1000 if match.group(2) == "ms" else 1)
        if abs(actual_us - expected_us) > 0.1:
            failures.append(namespace)
    return failures


def compile_harness() -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    binary = BUILD_DIR / "tls_network"
    checked(["gcc", "-O2", "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(OPENSSL_DIR / "include"), str(HARNESS_SOURCE), "-L", str(OPENSSL_DIR / "lib"), f"-Wl,-rpath,{OPENSSL_DIR / 'lib'}", "-lssl", "-lcrypto", "-o", str(binary)], env=local_env())
    return binary


def parse_result(text: str, count: int) -> list[str]:
    for line in text.splitlines():
        parts = line.split("\t")
        # ``count`` is the number of result values after the literal RESULT
        # record tag, not the total number of tab-separated fields.
        if parts and parts[0] == "RESULT" and len(parts) == count + 1:
            return parts[1:]
    raise RuntimeError(f"malformed harness output: {text[-800:]!r}")


def run_one(binary: Path, cfg: dict, case: dict, port: int) -> dict[str, str | int]:
    credential = ROOT / "credentials" / case["credential"]
    server = subprocess.Popen(namespace_command(cfg["server_namespace"], ["taskset", "-c", str(cfg["server_cpu"]), str(binary), "server", cfg["server_address"], str(port), str(credential.with_suffix(".cert.pem")), str(credential.with_suffix(".key.pem")), case["group"], case["signature"], "TLS_AES_128_GCM_SHA256"]), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
    try:
        if not select.select([server.stdout], [], [], 15)[0] or server.stdout.readline().strip() != "READY":
            _, stderr = server.communicate(timeout=3)
            raise RuntimeError(f"server readiness failed: {stderr[-800:]}")
        client = command(namespace_command(cfg["client_namespace"], ["taskset", "-c", str(cfg["client_cpu"]), str(binary), "client", cfg["server_address"], str(port), str(credential.with_suffix(".cert.pem")), case["hostname"], case["group"], case["signature"], "TLS_AES_128_GCM_SHA256"]), env=local_env(), timeout=35)
        server_stdout, server_stderr = server.communicate(timeout=35)
        client_data, server_data = parse_result(client.stdout, 9), parse_result(server_stdout, 5)
        valid = (client.returncode == 0 and server.returncode == 0 and client_data[0] == "1" and server_data[0] == "1" and client_data[1] == "TLSv1.3" and server_data[1] == "TLSv1.3" and client_data[2] == "TLS_AES_128_GCM_SHA256" and server_data[2] == "TLS_AES_128_GCM_SHA256" and client_data[3].lower() == case["group"].lower() and server_data[3].lower() == case["group"].lower() and client_data[4].lower() == case["signature"].lower() and server_data[4].lower() == case["signature"].lower())
        return {"case_id": case["case_id"], "tls_version": client_data[1], "cipher_suite": client_data[2], "requested_group": case["group"], "observed_group": client_data[3], "requested_signature_type": case["signature"], "observed_signature_type": client_data[4], "handshake_success_failure": "success" if valid else "failure", "tcp_connect_ns": client_data[5], "tls_handshake_ns": client_data[6], "handshake_bytes": client_data[7], "packet_count": client_data[8], "client_returncode": client.returncode, "server_returncode": server.returncode, "error_reason": "" if valid else (client.stderr + " " + server_stderr)[-600:]}
    finally:
        if server.poll() is None:
            server.kill()
        try:
            server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server.kill()


def preflight(cfg: dict) -> tuple[dict, Path | None]:
    helpers, checks, errors = load_final_helpers(), {}, []
    try:
        if not OPENSSL_BIN.is_file() or not OPENSSL_SOURCE.is_dir():
            raise RuntimeError("pinned OpenSSL source/install tree is missing")
        checks["openssl_version"] = checked([str(OPENSSL_BIN), "version"], env=local_env()).stdout.strip()
        checks["openssl_source_commit"] = checked(["git", "-C", str(OPENSSL_SOURCE), "rev-parse", "HEAD"]).stdout.strip()
        checks["topology"] = topology_snapshot(cfg)
        checks["qdisc"] = qdisc_snapshot(cfg)
        checks["credentials"] = helpers.credential_checks(cfg, local_env())
        checks["environment_snapshot"] = helpers.environment_snapshot()
        binary = compile_harness()
        checks["compiled_harness_sha256"] = sha256(binary)
        if cfg["required_openssl_version"] not in checks["openssl_version"]: errors.append("OpenSSL version differs from pinned requirement")
        if checks["openssl_source_commit"] != cfg["required_openssl_source_commit"]: errors.append("OpenSSL source commit differs from pinned requirement")
        if not all(item["ok"] for item in checks["credentials"]): errors.append("credential validation failed")
        errors.extend(helpers.guard_errors(checks["environment_snapshot"], cfg))
    except Exception as exc:
        errors.append(repr(exc)); binary = None
    return {"checks": checks, "errors": errors, "ready_to_collect": not errors}, binary


def write_json_exclusive(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def evidence_path(mode: str) -> Path:
    return EVIDENCE_ROOT / f"{mode}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"


def environment_errors(cfg: dict) -> tuple[dict, list[str]]:
    helpers = load_final_helpers()
    snapshot = helpers.environment_snapshot()
    return snapshot, helpers.guard_errors(snapshot, cfg)


def smoke(cfg: dict, preparation: dict, binary: Path) -> dict:
    condition = cfg["conditions"][0]
    set_delay(cfg, condition)
    before = qdisc_snapshot(cfg)
    rows = [run_one(binary, cfg, case, 31000 + index) for index, case in enumerate(cfg["cases"])]
    after, errors = environment_errors(cfg)
    return {"condition": condition, "qdisc": before, "qdisc_errors": qdisc_errors(condition, before), "rows": rows, "environment_after": after, "environment_errors": errors, "all_cases_passed": not qdisc_errors(condition, before) and not errors and all(row["handshake_success_failure"] == "success" for row in rows)}


def schedule(cfg: dict) -> list[dict]:
    items = [{"condition": condition, "condition_batch": number} for condition in cfg["conditions"] for number in range(1, int(cfg["batch_count"]) + 1)]
    random.Random(int(cfg["master_seed"])).shuffle(items)
    for index, item in enumerate(items, 1): item["collection_sequence"] = index
    return items


def collect(cfg: dict, preparation: dict, binary: Path) -> int:
    campaign = "campaign-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    raw_dir, meta_dir = RAW_ROOT / campaign, META_ROOT / campaign
    if raw_dir.exists() or meta_dir.exists(): raise RuntimeError("campaign identifier already exists")
    raw_dir.mkdir(parents=True); meta_dir.mkdir(parents=True)
    manifest = {"campaign_id": campaign, "status": "incomplete", "started_utc": utc_now(), "repository_commit": git_commit(), "preflight": preparation, "schedule": schedule(cfg), "completed_batches": [], "error": None}
    previous = False
    active_batch: dict | None = None
    try:
        for item in manifest["schedule"]:
            condition, number = item["condition"], item["condition_batch"]
            batch_id = f"{condition['condition_id']}-b{number:02d}"
            csv_path, metadata_path = raw_dir / f"{batch_id}.csv", meta_dir / f"{batch_id}.json"
            if previous: time.sleep(int(cfg["idle_seconds_between_batches"]))
            set_delay(cfg, condition)
            qbefore = qdisc_snapshot(cfg)
            environment_before, environment_guard_errors = environment_errors(cfg)
            guard_errors = qdisc_errors(condition, qbefore) + environment_guard_errors
            if guard_errors: raise RuntimeError(f"batch guard failure for {batch_id}: {guard_errors}")
            warmups = [(case, True) for case in cfg["cases"] for _ in range(int(cfg["warmups_per_case"]))]
            measured = [(case, False) for case in cfg["cases"] for _ in range(int(cfg["measured_per_case"]))]
            randomizer = random.Random(int(cfg["master_seed"]) + item["collection_sequence"])
            randomizer.shuffle(warmups)
            randomizer.shuffle(measured)
            planned = warmups + measured
            active_batch = {"campaign_id": campaign, "batch_id": batch_id, "status": "running", "condition": condition, "condition_batch": number, "collection_sequence": item["collection_sequence"], "rows_planned": len(planned), "rows_written": 0, "environment_before": environment_before, "qdisc_before": qbefore, "csv_path": str(csv_path.relative_to(ROOT)), "error": None}
            with csv_path.open("x", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader()
                for sequence, (case, warmup) in enumerate(planned, 1):
                    observed = run_one(binary, cfg, case, 32000 + sequence)
                    row = {field: "" for field in FIELDS}; row.update(observed); row.update({"condition_id": condition["condition_id"], "batch_id": batch_id, "run_id": campaign, "timestamp": utc_now(), "sequence_index": sequence, "warmup_flag": str(warmup).lower(), "git_commit_hash": manifest["repository_commit"], "openssl_version": preparation["checks"]["openssl_version"], "openssl_source_commit": preparation["checks"]["openssl_source_commit"]})
                    writer.writerow(row); handle.flush(); os.fsync(handle.fileno())
                    active_batch["rows_written"] += 1
                    if observed["handshake_success_failure"] != "success": raise RuntimeError(f"handshake failure in {batch_id}, sequence {sequence}")
            environment_after, end_environment_errors = environment_errors(cfg); qafter = qdisc_snapshot(cfg); end_qdisc_errors = qdisc_errors(condition, qafter)
            if end_environment_errors or end_qdisc_errors: raise RuntimeError(f"batch end guard failure for {batch_id}: {end_qdisc_errors + end_environment_errors}")
            metadata = {"campaign_id": campaign, "batch_id": batch_id, "status": "completed", "condition": condition, "condition_batch": number, "collection_sequence": item["collection_sequence"], "rows": len(planned), "environment_before": environment_before, "environment_after": environment_after, "qdisc_before": qbefore, "qdisc_after": qafter, "csv_path": str(csv_path.relative_to(ROOT)), "csv_sha256": sha256(csv_path)}
            write_json_exclusive(metadata_path, metadata)
            os.chmod(csv_path, 0o444)
            os.chmod(metadata_path, 0o444)
            manifest["completed_batches"].append(metadata); previous = True
            active_batch = None
        manifest["status"] = "complete"
    except BaseException as exc:
        manifest["error"] = repr(exc)
        if active_batch is not None:
            active_batch["status"] = "incomplete"
            active_batch["error"] = repr(exc)
            active_batch["ended_utc"] = utc_now()
            if "csv_path" in active_batch and (ROOT / active_batch["csv_path"]).exists():
                active_batch["csv_sha256"] = sha256(ROOT / active_batch["csv_path"])
            incomplete = meta_dir / f"{active_batch['batch_id']}-incomplete.json"
            write_json_exclusive(incomplete, active_batch)
        raise
    finally:
        manifest["ended_utc"] = utc_now(); write_json_exclusive(meta_dir / f"{campaign}.json", manifest)
    print(json.dumps({"campaign_id": campaign, "status": manifest["status"]}, indent=2)); return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"--preflight-only", "--smoke-test", "--run"}:
        print("Usage: run_network.py --preflight-only|--smoke-test|--run", file=sys.stderr); return 2
    mode, cfg = sys.argv[1], json.loads(CONFIG.read_text(encoding="utf-8"))
    preparation, binary = preflight(cfg)
    record = {"workflow": "network-sensitivity-v1", "mode": mode, "captured_utc": utc_now(), "repository_commit": git_commit(), "configuration_path": str(CONFIG.relative_to(ROOT)), "configuration_sha256": sha256(CONFIG), **preparation}
    if mode == "--preflight-only":
        path = evidence_path("preflight"); write_json_exclusive(path, record); print(json.dumps({"ready_to_collect": record["ready_to_collect"], "evidence_path": str(path.relative_to(ROOT)), "errors": record["errors"]}, indent=2)); return 0 if record["ready_to_collect"] else 1
    if not record["ready_to_collect"]:
        print(json.dumps(record, indent=2), file=sys.stderr); return 1
    if mode == "--smoke-test":
        record["smoke"] = smoke(cfg, preparation, binary); record["ready_to_collect"] = record["smoke"]["all_cases_passed"]
        path = evidence_path("smoke"); write_json_exclusive(path, record); print(json.dumps({"ready_to_collect": record["ready_to_collect"], "evidence_path": str(path.relative_to(ROOT))}, indent=2)); return 0 if record["ready_to_collect"] else 1
    return collect(cfg, preparation, binary)


if __name__ == "__main__":
    raise SystemExit(main())
