#!/usr/bin/env python3
"""Guarded Windows collection for the separate cross-platform validation.

Preflight and smoke modes create evidence only.  Each --run creates a new,
non-resumable campaign; it never merges with an earlier Windows campaign.
"""
from __future__ import annotations

import csv
import ctypes
import datetime as dt
import hashlib
import json
import os
import random
import re
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs" / "windows" / "final.json"
OPENSSL_ROOT = ROOT / "third_party" / "openssl-3.5.9"
OPENSSL_BIN = OPENSSL_ROOT / "install" / "bin" / "openssl.exe"
OPENSSL_SOURCE = OPENSSL_ROOT / "source"
OPENSSL_BIN_DIR = OPENSSL_BIN.parent
HARNESS_SOURCE = ROOT / "scripts" / "windows" / "tls_windows.c"
TOPOLOGY_SOURCE = ROOT / "scripts" / "windows" / "cpu_topology_windows.c"
BUILD_DIR = ROOT / "build" / "windows-final"
RAW_ROOT = ROOT / "data" / "raw" / "windows"
META_ROOT = ROOT / "data" / "metadata" / "windows"
EVIDENCE_ROOT = ROOT / "evidence" / "windows-final-workflow"
VCVARS = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat")


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, check=check)


def local_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = str(OPENSSL_BIN_DIR) + os.pathsep + env.get("PATH", "")
    return env


def git_commit() -> str:
    return run(["git", "rev-parse", "HEAD"]).stdout.strip()


def power_status() -> dict:
    class Status(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_byte), ("BatteryFlag", ctypes.c_byte),
                    ("BatteryLifePercent", ctypes.c_byte), ("SystemStatusFlag", ctypes.c_byte),
                    ("BatteryLifeTime", ctypes.c_uint32), ("BatteryFullLifeTime", ctypes.c_uint32)]
    status = Status()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        raise RuntimeError("GetSystemPowerStatus failed")
    return {"ac_line_status": int(status.ACLineStatus), "battery_percent": int(status.BatteryLifePercent),
            "battery_flag": int(status.BatteryFlag), "system_status_flag": int(status.SystemStatusFlag)}


def active_power_scheme() -> dict:
    text = run(["powercfg", "/getactivescheme"]).stdout.strip()
    match = re.search(r"([0-9a-fA-F-]{36})\s+\((.*)\)", text)
    return {"raw": text, "guid": match.group(1).lower() if match else None,
            "name": match.group(2) if match else None}


def compile_c(source: Path, output: Path, *, openssl: bool) -> None:
    if not VCVARS.is_file():
        raise RuntimeError(f"Visual Studio build environment missing: {VCVARS}")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    if openssl:
        compile_line = (f'cl /nologo /std:c11 /O2 /W4 /WX '
                        f'/I "{OPENSSL_ROOT / "install" / "include"}" "{source}" '
                        f'/link /OUT:"{output}" /LIBPATH:"{OPENSSL_ROOT / "install" / "lib"}" '
                        'libssl.lib libcrypto.lib ws2_32.lib')
    else:
        compile_line = f'cl /nologo /std:c11 /O2 /W4 /WX "{source}" /link /OUT:"{output}"'
    # A temporary batch file avoids cmd.exe's fragile quote handling when its
    # command argument itself begins with the quoted Visual Studio path.
    batch = BUILD_DIR / "compile_windows_temp.cmd"
    batch.write_text(f'@echo off\r\ncall "{VCVARS}" >nul || exit /b 1\r\n{compile_line}\r\n', encoding="ascii", newline="")
    completed = run(["cmd.exe", "/d", "/c", str(batch)], check=False)
    if completed.returncode:
        raise RuntimeError(f"C compilation failed for {source.name}:\n{completed.stdout}\n{completed.stderr}")


def build_tools() -> tuple[Path, Path]:
    harness, topology = BUILD_DIR / "tls_windows.exe", BUILD_DIR / "cpu_topology_windows.exe"
    compile_c(HARNESS_SOURCE, harness, openssl=True)
    compile_c(TOPOLOGY_SOURCE, topology, openssl=False)
    return harness, topology


def processor_topology(tool: Path) -> list[dict]:
    completed = run([str(tool)])
    rows = []
    for line in completed.stdout.splitlines():
        if not line.startswith("CPUSET\t"):
            continue
        values = dict(field.split("=", 1) for field in line.split("\t")[1:] if "=" in field)
        rows.append({key: int(value) for key, value in values.items()})
    if not rows:
        raise RuntimeError("Windows CPU-set topology query returned no processor rows")
    return rows


def select_affinity(rows: list[dict]) -> dict:
    usable = [row for row in rows if row["group"] == 0 and not row["parked"] and not row["allocated"] and row["logical_processor"] != 0]
    if not usable:
        raise RuntimeError("no usable group-0 processor sets outside logical processor 0")
    # Microsoft defines larger EfficiencyClass values as faster, less
    # energy-efficient processors on heterogeneous systems.
    best_efficiency = max(row["efficiency_class"] for row in usable)
    candidates = [row for row in usable if row["efficiency_class"] == best_efficiency]
    selected = []
    seen_cores: set[int] = set()
    for row in sorted(candidates, key=lambda item: (item["core"], item["logical_processor"])):
        if row["core"] not in seen_cores:
            selected.append(row)
            seen_cores.add(row["core"])
        if len(selected) == 2:
            break
    if len(selected) != 2:
        raise RuntimeError("topology does not provide two distinct active highest-performance cores")
    return {"efficiency_class": best_efficiency, "client": selected[0], "server": selected[1],
            "client_mask": 1 << selected[0]["logical_processor"],
            "server_mask": 1 << selected[1]["logical_processor"], "all_rows": rows}


def background_snapshot() -> list[dict]:
    code = "Get-Process | Sort-Object CPU -Descending | Select-Object -First 16 ProcessName,Id,CPU | ConvertTo-Json -Compress"
    completed = run(["powershell.exe", "-NoProfile", "-Command", code], check=False)
    if completed.returncode or not completed.stdout.strip():
        return []
    result = json.loads(completed.stdout)
    return result if isinstance(result, list) else [result]


def environment_snapshot(topology: dict) -> dict:
    return {"captured_utc": utc_now(), "power": power_status(), "active_power_scheme": active_power_scheme(),
            "selected_affinity": topology, "top_processes_by_cpu_time": background_snapshot(),
            "os": run(["cmd.exe", "/d", "/c", "ver"]).stdout.strip()}


def parse_fields(text: str, marker: str) -> dict:
    for line in text.splitlines():
        if line.startswith(marker + "\t"):
            return dict(item.split("=", 1) for item in line.split("\t")[1:] if "=" in item)
    return {}


def credential_checks(env: dict[str, str], cfg: dict) -> list[dict]:
    output = []
    seen = set()
    for case in cfg["cases"]:
        if case["credential"] in seen:
            continue
        seen.add(case["credential"])
        base = ROOT / "credentials" / "windows-validation" / case["credential"]
        cert, key = base.with_suffix(".cert.pem"), base.with_suffix(".key.pem")
        item = {"credential": case["credential"], "certificate": str(cert.relative_to(ROOT)),
                "certificate_sha256": sha256(cert) if cert.is_file() else None, "ok": False, "errors": []}
        try:
            if not cert.is_file() or not key.is_file():
                raise RuntimeError("certificate or private key is missing")
            run([str(OPENSSL_BIN), "x509", "-in", str(cert), "-noout", "-checkend", "0"], env=env)
            cert_pub = run([str(OPENSSL_BIN), "x509", "-in", str(cert), "-pubkey", "-noout"], env=env).stdout.strip()
            key_pub = run([str(OPENSSL_BIN), "pkey", "-in", str(key), "-pubout"], env=env).stdout.strip()
            if cert_pub != key_pub:
                raise RuntimeError("certificate public key does not match private key")
            item["ok"] = True
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            item["errors"].append(str(exc))
        output.append(item)
    return output


def guard_errors(snapshot: dict, cfg: dict) -> list[str]:
    errors = []
    if snapshot["power"]["ac_line_status"] != 1:
        errors.append("AC power is not online")
    name = snapshot["active_power_scheme"]["name"]
    if name != cfg["required_power_scheme_name"]:
        errors.append(f"active power scheme must be {cfg['required_power_scheme_name']!r}, observed {name!r}")
    selection = snapshot["selected_affinity"]
    if selection["client"]["core"] == selection["server"]["core"]:
        errors.append("client and server selected the same physical core")
    return errors


def choose_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def one_handshake(binary: Path, case: dict, affinity: dict, env: dict[str, str]) -> dict:
    base = ROOT / "credentials" / "windows-validation" / case["credential"]
    cert, key = base.with_suffix(".cert.pem"), base.with_suffix(".key.pem")
    port = choose_port()
    server_cmd = [str(binary), "server", str(port), str(cert), str(key), case["group"], case["signature"],
                  "--affinity-mask", hex(affinity["server_mask"])]
    client_cmd = [str(binary), "client", str(port), str(cert), case["hostname"], case["group"], case["signature"],
                  "--affinity-mask", hex(affinity["client_mask"])]
    server = subprocess.Popen(server_cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    ready = ""
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        line = server.stdout.readline() if server.stdout else ""
        ready += line
        if line.startswith("READY\t"):
            break
        if server.poll() is not None:
            break
    if "READY\t" not in ready:
        stdout, stderr = server.communicate(timeout=2)
        raise RuntimeError(f"server did not become ready: {ready}{stdout}\n{stderr}")
    client = run(client_cmd, env=env, check=False)
    server_stdout, server_stderr = server.communicate(timeout=15)
    client_fields = parse_fields(client.stdout, "CLIENT_RESULT")
    server_fields = parse_fields(server_stdout, "SERVER_RESULT")
    return {"client_returncode": client.returncode, "server_returncode": server.returncode,
            "client": client_fields, "server": server_fields,
            "client_stderr": client.stderr.strip(), "server_stderr": server_stderr.strip(),
            "server_ready": parse_fields(ready, "READY")}


def validate(case: dict, result: dict, affinity: dict) -> tuple[bool, list[str]]:
    client, server = result["client"], result["server"]
    expected = {"tls_version": "TLSv1.3", "cipher": "TLS_AES_128_GCM_SHA256", "group": case["group"],
                "certificate_verify_signature_scheme": case["signature"], "peer_public_key_type": case["key_type"]}
    errors = []
    if result["client_returncode"] != 0 or result["server_returncode"] != 0:
        errors.append("nonzero process return code")
    if client.get("success") != "1" or client.get("chain_result") != "PASS" or client.get("hostname_result") != "PASS":
        errors.append("client success or certificate verification failed")
    for key, wanted in expected.items():
        if client.get(key) != wanted:
            errors.append(f"client {key}={client.get(key)!r}, expected {wanted!r}")
    for key in ("tls_version", "cipher", "group", "signature"):
        wanted = {"tls_version": "TLSv1.3", "cipher": "TLS_AES_128_GCM_SHA256", "group": case["group"], "signature": case["signature"]}[key]
        if server.get(key) != wanted:
            errors.append(f"server {key}={server.get(key)!r}, expected {wanted!r}")
    if client.get("affinity_mask") != hex(affinity["client_mask"]) or server.get("affinity_mask") != hex(affinity["server_mask"]):
        errors.append("reported affinity mask differs from requested mask")
    try:
        if int(client["qpc_stop"]) <= int(client["qpc_start"]) or int(client["qpc_frequency"]) <= 0:
            errors.append("invalid QPC timing fields")
    except (KeyError, ValueError):
        errors.append("missing QPC timing fields")
    return not errors, errors


def write_json_exclusive(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def preflight(cfg: dict) -> tuple[dict, Path, dict[str, str]]:
    env = local_env()
    harness, topology_tool = build_tools()
    topology = select_affinity(processor_topology(topology_tool))
    snapshot = environment_snapshot(topology)
    checks = {"openssl_version": run([str(OPENSSL_BIN), "version"], env=env).stdout.strip(),
              "openssl_source_commit": run(["git", "-C", str(OPENSSL_SOURCE), "rev-parse", "HEAD"]).stdout.strip(),
              "harness_sha256": sha256(harness), "topology_tool_sha256": sha256(topology_tool),
              "credentials": credential_checks(env, cfg), "environment_snapshot": snapshot}
    errors = guard_errors(snapshot, cfg)
    if cfg["required_openssl_version"] not in checks["openssl_version"]:
        errors.append("pinned OpenSSL version check failed")
    if checks["openssl_source_commit"] != cfg["required_openssl_source_commit"]:
        errors.append("pinned OpenSSL source commit check failed")
    if not all(item["ok"] for item in checks["credentials"]):
        errors.append("credential validation failed")
    return {"checks": checks, "errors": errors, "ready_to_collect": not errors}, harness, env


def evidence(mode: str, data: dict) -> Path:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = EVIDENCE_ROOT / f"{mode}-{stamp}.json"
    write_json_exclusive(path, data)
    return path


def smoke(cfg: dict, prep: dict, harness: Path, env: dict[str, str]) -> dict:
    results = []
    for case in cfg["cases"]:
        item = one_handshake(harness, case, prep["checks"]["environment_snapshot"]["selected_affinity"], env)
        ok, errors = validate(case, item, prep["checks"]["environment_snapshot"]["selected_affinity"])
        results.append({"case_id": case["case_id"], "ok": ok, "errors": errors, "result": item})
    return {"case_results": results, "all_cases_passed": all(row["ok"] for row in results),
            "environment_after": environment_snapshot(prep["checks"]["environment_snapshot"]["selected_affinity"])}


def collect(cfg: dict, prep: dict, harness: Path, env: dict[str, str]) -> int:
    campaign = "campaign-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:12]
    raw_dir, meta_dir = RAW_ROOT / campaign, META_ROOT / campaign
    if raw_dir.exists() or meta_dir.exists():
        raise RuntimeError("new campaign identifier already exists")
    affinity = prep["checks"]["environment_snapshot"]["selected_affinity"]
    metadata = {"workflow": "windows-final-validation", "campaign_id": campaign, "started_utc": utc_now(),
                "repository_commit": git_commit(), "configuration_sha256": sha256(CONFIG), "preflight": prep,
                "batches": []}
    randomizer = random.Random(cfg["master_seed"])
    fields = ["batch_id", "run_id", "timestamp", "case_id", "sequence_index", "warmup_flag", "qpc_ticks", "qpc_frequency", "latency_ns", "client_returncode", "server_returncode", "validation_ok", "validation_errors", "client_affinity_mask", "server_affinity_mask", "tls_version", "cipher_suite", "observed_group", "peer_public_key_type", "certificate_verify_signature_scheme", "chain_result", "hostname_result", "server_group", "server_signature", "client_stderr", "server_stderr"]
    raw_dir.mkdir(parents=True)
    try:
        for batch_num in range(1, cfg["batch_count"] + 1):
            current = environment_snapshot(affinity)
            errors = guard_errors(current, cfg)
            if errors:
                raise RuntimeError("batch guard failure: " + "; ".join(errors))
            rows = [(case, True) for case in cfg["cases"] for _ in range(cfg["warmups_per_case"])] + [(case, False) for case in cfg["cases"] for _ in range(cfg["measured_per_case"])]
            randomizer.shuffle(rows)
            csv_path = raw_dir / f"{campaign}-b{batch_num:02d}.csv"
            with csv_path.open("x", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for index, (case, warmup) in enumerate(rows, 1):
                    result = one_handshake(harness, case, affinity, env)
                    ok, validation_errors = validate(case, result, affinity)
                    client, server = result["client"], result["server"]
                    try:
                        ticks = int(client.get("qpc_stop", "0")) - int(client.get("qpc_start", "0")); frequency = int(client.get("qpc_frequency", "0"))
                    except ValueError:
                        ticks, frequency = 0, 0
                    writer.writerow({"batch_id": f"b{batch_num:02d}", "run_id": f"b{batch_num:02d}-{index:04d}", "timestamp": utc_now(), "case_id": case["case_id"], "sequence_index": index, "warmup_flag": str(warmup).lower(), "qpc_ticks": ticks, "qpc_frequency": frequency, "latency_ns": (ticks * 1_000_000_000 // frequency) if frequency else "", "client_returncode": result["client_returncode"], "server_returncode": result["server_returncode"], "validation_ok": str(ok).lower(), "validation_errors": "; ".join(validation_errors), "client_affinity_mask": client.get("affinity_mask", ""), "server_affinity_mask": server.get("affinity_mask", ""), "tls_version": client.get("tls_version", ""), "cipher_suite": client.get("cipher", ""), "observed_group": client.get("group", ""), "peer_public_key_type": client.get("peer_public_key_type", ""), "certificate_verify_signature_scheme": client.get("certificate_verify_signature_scheme", ""), "chain_result": client.get("chain_result", ""), "hostname_result": client.get("hostname_result", ""), "server_group": server.get("group", ""), "server_signature": server.get("signature", ""), "client_stderr": result["client_stderr"], "server_stderr": result["server_stderr"]})
                    if not ok:
                        raise RuntimeError(f"handshake validation failed in b{batch_num:02d}, sequence {index}: {validation_errors}")
            metadata["batches"].append({"batch_id": f"b{batch_num:02d}", "csv": str(csv_path.relative_to(ROOT)), "sha256": sha256(csv_path), "environment_before": current, "environment_after": environment_snapshot(affinity)})
            if batch_num != cfg["batch_count"]:
                time.sleep(cfg["idle_seconds_between_batches"])
    except BaseException as exc:
        metadata["status"] = "incomplete"
        metadata["error"] = repr(exc)
        metadata["ended_utc"] = utc_now()
        meta_dir.mkdir(parents=True, exist_ok=True)
        write_json_exclusive(meta_dir / f"{campaign}-incomplete.json", metadata)
        raise
    metadata["status"] = "complete"; metadata["ended_utc"] = utc_now()
    meta_dir.mkdir(parents=True, exist_ok=True)
    write_json_exclusive(meta_dir / f"{campaign}.json", metadata)
    print(json.dumps({"campaign_id": campaign, "status": "complete", "raw_directory": str(raw_dir.relative_to(ROOT)), "metadata": str((meta_dir / f"{campaign}.json").relative_to(ROOT))}, indent=2))
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"--preflight-only", "--smoke-test", "--run"}:
        print("Usage: run_final_windows.py --preflight-only|--smoke-test|--run", file=sys.stderr); return 2
    cfg = json.loads(CONFIG.read_text(encoding="utf-8")); mode = sys.argv[1]
    try:
        prep, harness, env = preflight(cfg)
    except BaseException as exc:
        print(f"preflight setup failed: {exc}", file=sys.stderr); return 1
    record = {"workflow": "windows-final-validation", "mode": mode, "captured_utc": utc_now(), "repository_commit": git_commit(), "configuration_path": str(CONFIG.relative_to(ROOT)), "configuration_sha256": sha256(CONFIG), **prep}
    if mode == "--preflight-only":
        path = evidence("preflight", record); print(json.dumps({**record, "evidence_path": str(path.relative_to(ROOT))}, indent=2)); return 0 if prep["ready_to_collect"] else 1
    if not prep["ready_to_collect"]:
        print(json.dumps(record, indent=2), file=sys.stderr); return 1
    if mode == "--smoke-test":
        record["smoke_test"] = smoke(cfg, prep, harness, env); record["ready_to_collect"] = record["smoke_test"]["all_cases_passed"]
        path = evidence("smoke-test", record); print(json.dumps({"ready_to_collect": record["ready_to_collect"], "evidence_path": str(path.relative_to(ROOT))}, indent=2)); return 0 if record["ready_to_collect"] else 1
    return collect(cfg, prep, harness, env)


if __name__ == "__main__":
    raise SystemExit(main())
