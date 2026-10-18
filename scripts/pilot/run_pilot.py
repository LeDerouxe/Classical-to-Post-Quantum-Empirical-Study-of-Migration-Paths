#!/usr/bin/env python3
"""Build the pinned-OpenSSL C harness and collect one immutable Phase 2 pilot."""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import random
import re
import select
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/pilot/pilot.json"
OPENSSL_DIR = ROOT / "third_party/openssl-3.5.9/install"
OPENSSL_BIN = OPENSSL_DIR / "bin/openssl"
HARNESS_SOURCE = ROOT / "scripts/pilot/tls_pilot.c"
BUILD_DIR = ROOT / "build/pilot"
DATA_DIR = ROOT / "data/raw/pilot"
METADATA_DIR = ROOT / "data/metadata/pilot"
FIELDS = [
    "run_id", "timestamp", "case_id", "sequence_index", "warmup_flag",
    "git_commit_hash", "openssl_version", "openssl_source_commit", "tls_version",
    "cipher_suite", "requested_group", "observed_group", "requested_signature_type",
    "observed_signature_type", "handshake_success_failure", "tcp_connect_ns",
    "tls_handshake_ns", "client_user_cpu_ns", "client_system_cpu_ns",
    "server_user_cpu_ns", "server_system_cpu_ns", "client_peak_rss_kib",
    "server_peak_rss_kib", "handshake_bytes", "packet_count", "error_reason",
]
CASES = None


def checked(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, text=True, **kwargs)


def compile_harness() -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    binary = BUILD_DIR / "tls_pilot"
    cmd = ["gcc", "-O2", "-std=c11", "-Wall", "-Wextra", "-I", str(OPENSSL_DIR / "include"),
           str(HARNESS_SOURCE), "-L", str(OPENSSL_DIR / "lib"),
           f"-Wl,-rpath,{OPENSSL_DIR / 'lib'}", "-lssl", "-lcrypto", "-o", str(binary)]
    checked(cmd)
    return binary


def parse_result(line: str, expected_fields: int) -> list[str]:
    parts = line.rstrip("\n").split("\t")
    if len(parts) != expected_fields or parts[0] != "RESULT":
        raise RuntimeError(f"Malformed harness result: {line!r}")
    return parts[1:]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def server_result(binary: Path, case: dict, env: dict, port: int,
                  server_cpu: int) -> tuple[list[str], str]:
    credential = ROOT / "credentials" / case["credential"]
    server_cmd = ["taskset", "-c", str(server_cpu), str(binary), "server", str(port),
                  str(credential.with_suffix(".cert.pem")), str(credential.with_suffix(".key.pem")),
                  case["group"], case["signature"], "TLS_AES_128_GCM_SHA256"]
    proc = subprocess.Popen(server_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, env=env, bufsize=1)
    ready, _, _ = select.select([proc.stdout], [], [], 10)
    if not ready:
        proc.kill()
        stderr = proc.communicate()[1]
        raise RuntimeError(f"Server startup timed out: {stderr[-1000:]}")
    first = proc.stdout.readline()
    if first.strip() != "READY":
        stderr = proc.communicate(timeout=3)[1]
        raise RuntimeError(f"Server did not become ready: {first.strip()} {stderr[-1000:]}")
    return proc, ""


def one_observation(binary: Path, case: dict, env: dict, client_cpu: int,
                    server_cpu: int) -> tuple[dict[str, str], str]:
    port = free_port()
    server, _ = server_result(binary, case, env, port, server_cpu)
    credential = ROOT / "credentials" / case["credential"]
    client_cmd = ["taskset", "-c", str(client_cpu), str(binary), "client", str(port),
                  str(credential.with_suffix(".cert.pem")), case["hostname"], case["group"],
                  case["signature"], "TLS_AES_128_GCM_SHA256"]
    try:
        client = subprocess.run(client_cmd, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=15, env=env, check=False)
        out_line = next((line for line in client.stdout.splitlines() if line.startswith("RESULT\t")), None)
        if out_line is None:
            raise RuntimeError(f"Client produced no result (rc={client.returncode}): {client.stderr[-1000:]}")
        c = parse_result(out_line, 16)
        ready, _, _ = select.select([server.stdout], [], [], 15)
        if not ready:
            server.kill()
            _, stderr = server.communicate()
            raise RuntimeError(f"Server handshake timed out: {stderr[-1000:]}")
        line = server.stdout.readline()
        s = parse_result(line, 14)
        rest, stderr = server.communicate(timeout=5)
        if "TCP_INFO unavailable" in c[14] or "TCP_INFO unavailable" in s[12]:
            raise RuntimeError("TCP_INFO counters unavailable; stop before collecting pilot data")
        ok = c[0] == "1" and s[0] == "1" and client.returncode == 0
        if ok:
            expected_tls = "TLSv1.3"
            expected_sig = case["signature"].lower()
            if c[1] != expected_tls or s[1] != expected_tls:
                raise RuntimeError(f"Unexpected TLS version: client={c[1]} server={s[1]}")
            if c[2] != "TLS_AES_128_GCM_SHA256" or s[2] != "TLS_AES_128_GCM_SHA256":
                raise RuntimeError(f"Unexpected cipher suite: client={c[2]} server={s[2]}")
            if c[3].lower() != case["group"].lower() or s[3].lower() != case["group"].lower():
                raise RuntimeError(f"Unexpected group: requested={case['group']} client={c[3]} server={s[3]}")
            if c[4].lower() != expected_sig or s[4].lower() != expected_sig:
                raise RuntimeError(f"Unexpected signature scheme: requested={case['signature']} client={c[4]} server={s[4]}")
        # Use one endpoint consistently. Linux TCP_INFO at the server can count
        # the SYN sequence-space byte as received payload, so server/client
        # receive counters are not directionally reconcilable on loopback.
        # Client counters are sampled immediately after SSL_connect and were
        # validated against loopback packet capture in the instrumentation smoke.
        tcp_bytes = int(c[10]) + int(c[11])
        packets = int(c[12]) + int(c[13])
        row = {
            "case_id": case["case_id"], "tls_version": c[1], "cipher_suite": c[2],
            "requested_group": case["group"], "observed_group": c[3],
            "requested_signature_type": case["signature"], "observed_signature_type": c[4],
            "handshake_success_failure": "success" if ok else "failure", "tcp_connect_ns": c[5],
            "tls_handshake_ns": c[6], "client_user_cpu_ns": c[7],
            "client_system_cpu_ns": c[8], "client_peak_rss_kib": c[9],
            "server_user_cpu_ns": s[5], "server_system_cpu_ns": s[6],
            "server_peak_rss_kib": s[7], "handshake_bytes": str(tcp_bytes),
            "packet_count": str(packets),
            "error_reason": "" if ok else f"client: {c[14]}; server: {s[12]}; client stderr: {client.stderr.strip()[-300:]}; server stderr: {stderr.strip()[-300:]}",
        }
        return row, ""
    finally:
        if server.poll() is None:
            server.kill()
        try:
            server.wait(timeout=2)
        except subprocess.TimeoutExpired:
            server.kill()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) == 2 else "run"
    if mode not in {"run", "--prepare-only", "--smoke-test"}:
        raise SystemExit("Usage: run_pilot.py [--prepare-only|--smoke-test]")
    cfg = json.loads(CONFIG.read_text())
    if not OPENSSL_BIN.is_file():
        raise SystemExit(f"Pinned research OpenSSL missing: {OPENSSL_BIN}")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    binary = compile_harness()
    if mode == "--prepare-only":
        print(f"Harness compiled successfully: {binary}")
        return
    for case in cfg["cases"]:
        credential = ROOT / "credentials" / case["credential"]
        for suffix in (".cert.pem", ".key.pem"):
            if not credential.with_suffix(suffix).is_file():
                raise SystemExit(f"Required ignored local credential missing: {credential.with_suffix(suffix)}")
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(OPENSSL_DIR / "lib")
    env["OPENSSL_CONF"] = str(ROOT / "configs/openssl/feasibility-openssl.cnf")
    if mode == "--smoke-test":
        for case in cfg["cases"]:
            smoke, error = one_observation(binary, case, env,
                                           cfg["client_cpu"], cfg["server_cpu"])
            if error or smoke.get("handshake_success_failure") != "success":
                raise SystemExit(f"Harness smoke test failed for {case['case_id']}: {error or smoke}")
            print(f"{case['case_id']}: success; bytes={smoke['handshake_bytes']}; packets={smoke['packet_count']}; group={smoke['observed_group']}; signature={smoke['observed_signature_type']}")
        print("Harness smoke tests passed for all cases; no pilot CSV or benchmark record was created.")
        return
    run_id = dt.datetime.now(dt.timezone.utc).strftime("pilot-%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
    seed = int(cfg["random_seed"])
    measured = [case for case in cfg["cases"] for _ in range(cfg["measured_runs_per_case"])]
    random.Random(seed).shuffle(measured)
    sequence = [(case, True) for case in cfg["cases"] for _ in range(cfg["warmups_per_case"])]
    sequence.extend((case, False) for case in measured)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / f"{run_id}.csv"
    metadata_path = METADATA_DIR / f"{run_id}.json"
    if csv_path.exists() or metadata_path.exists():
        raise SystemExit(f"Run output already exists; refusing overwrite: {run_id}")
    commit = checked(["git", "rev-parse", "HEAD"], cwd=ROOT, stdout=subprocess.PIPE).stdout.strip()
    version = checked([str(OPENSSL_BIN), "version"], cwd=ROOT, env=env,
                      stdout=subprocess.PIPE).stdout.strip()
    source_commit = checked(["git", "-C", str(OPENSSL_DIR / "source"), "rev-parse", "HEAD"],
                            stdout=subprocess.PIPE).stdout.strip()
    rows = []
    measured_index = 0
    for index, (case, warmup) in enumerate(sequence, start=1):
        data, error = one_observation(binary, case, env, cfg["client_cpu"], cfg["server_cpu"])
        if error:
            raise SystemExit(f"Handshake failed; no completed pilot CSV written. Sequence {index}, case {case['case_id']}: {error}")
        timestamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")
        row = {field: "" for field in FIELDS}
        row.update(data)
        row.update({"run_id": run_id, "timestamp": timestamp,
                    "sequence_index": index, "warmup_flag": str(warmup).lower(),
                    "git_commit_hash": commit, "openssl_version": version,
                    "openssl_source_commit": source_commit})
        rows.append(row)
        if not warmup:
            measured_index += 1
            print(f"measured {measured_index}/120: {case['case_id']}", flush=True)
    # Write once with exclusive creation, then never overwrite a completed run.
    fd = os.open(csv_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(fd, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.chmod(csv_path, 0o444)
    metadata = {
        "run_id": run_id, "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "git_commit_hash": commit, "openssl_version": version,
        "openssl_source_commit": source_commit, "config_path": "configs/pilot/pilot.json",
        "harness_source": "scripts/pilot/tls_pilot.c", "random_seed": seed,
        "warmups": cfg["warmups_per_case"], "measured_per_case": cfg["measured_runs_per_case"],
        "client_cpu": cfg["client_cpu"], "server_cpu": cfg["server_cpu"],
        "csv_path": str(csv_path.relative_to(ROOT)), "csv_sha256": __import__("hashlib").sha256(csv_path.read_bytes()).hexdigest(),
        "rows_total": len(rows), "measured_rows": measured_index,
    }
    fd = os.open(metadata_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(fd, "w") as f:
        json.dump(metadata, f, indent=2)
        f.write("\n")
    os.chmod(metadata_path, 0o444)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
