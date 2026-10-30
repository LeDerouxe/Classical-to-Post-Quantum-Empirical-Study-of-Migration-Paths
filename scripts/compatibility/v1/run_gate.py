#!/usr/bin/env python3
"""Compile and run only the mandatory Follow-up Study A dual-certificate gate."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VERSION_DIR = ROOT / "scripts/compatibility/v1"
CONFIG_PATH = ROOT / "configs/compatibility/v1/profiles.json"
SOURCE_PATH = VERSION_DIR / "tls_compat_gate.c"
INSTALL = ROOT / "third_party/openssl-3.5.9/install"
OPENSSL_SOURCE = ROOT / "third_party/openssl-3.5.9/source"
EXPECTED_OPENSSL_COMMIT = "45e844fa2a14ec92d146bd8f5778ac130b6625fb"
CERT_EC = ROOT / "credentials/ecdsa.cert.pem"
KEY_EC = ROOT / "credentials/ecdsa.key.pem"
CERT_MLDSA = ROOT / "credentials/mldsa.cert.pem"
KEY_MLDSA = ROOT / "credentials/mldsa.key.pem"
EXPECTED_REPO_COMMIT = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd(args: list[str], *, timeout: int = 10) -> dict:
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return {"argv": args, "returncode": result.returncode,
                "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"argv": args, "returncode": None, "stdout": "", "stderr": str(exc)}


def read(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return None


def cpu_list() -> list[int]:
    value = read(Path("/sys/devices/system/cpu/online")) or ""
    cpus: list[int] = []
    for part in value.split(","):
        bounds = [int(x) for x in part.split("-")]
        cpus.extend(range(bounds[0], bounds[-1] + 1))
    return cpus


def environment_snapshot() -> dict:
    policies = {}
    for path in sorted(Path("/sys/devices/system/cpu/cpufreq").glob("policy*")):
        policies[path.name] = {
            key: read(path / key) for key in (
                "related_cpus", "scaling_governor", "energy_performance_preference",
                "scaling_min_freq", "scaling_max_freq", "scaling_cur_freq")
        }
    topology = {}
    for cpu in cpu_list():
        base = Path(f"/sys/devices/system/cpu/cpu{cpu}")
        topology[str(cpu)] = {
            "online": read(base / "online") if cpu else "1",
            "thread_siblings_list": read(base / "topology/thread_siblings_list"),
            "core_id": read(base / "topology/core_id"),
            "physical_package_id": read(base / "topology/physical_package_id"),
            "current_frequency_khz": read(base / "cpufreq/scaling_cur_freq"),
        }
    supplies = {}
    for path in sorted(Path("/sys/class/power_supply").glob("*")):
        vals = {k: read(path / k) for k in ("type", "online", "status", "capacity")
                if (path / k).exists()}
        if vals:
            supplies[path.name] = vals
    thermal = {}
    for path in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        raw = read(path / "temp")
        if raw is not None:
            try:
                thermal[path.name] = {"type": read(path / "type"), "temp_c": int(raw) / 1000}
            except ValueError:
                thermal[path.name] = {"type": read(path / "type"), "raw": raw}
    try:
        processes = subprocess.run(["ps", "-eo", "comm=,%cpu=", "--sort=-%cpu"],
                                   capture_output=True, text=True, timeout=5, check=True).stdout.splitlines()[:20]
    except (OSError, subprocess.SubprocessError):
        processes = []
    try:
        load = list(os.getloadavg())
    except OSError:
        load = None
    return {
        "captured_utc": utc_now(),
        "platform": platform.platform(),
        "uname": platform.uname()._asdict(),
        "ac_battery": supplies,
        "power_profile": cmd(["powerprofilesctl", "get"]),
        "platform_profile": read(Path("/sys/firmware/acpi/platform_profile")),
        "cpu_policies": policies,
        "topology": topology,
        "load_average_1_5_15": load,
        "thermal_zones": thermal,
        "top_running_process_summary": processes,
        "affinity_plan": {"server_cpu": 4, "client_cpu": 2, "cpu0_reserved_for_os": True},
    }


def base_manifest(commit: str) -> dict[str, str]:
    paths = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.splitlines()
    result = {}
    for name in paths:
        path = ROOT / name
        if path.is_file():
            result[name] = sha256(path)
    return result


def parse_fields(line: str, prefix: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    if not line.startswith(prefix + "\t"):
        return fields
    for item in line.split("\t")[1:]:
        if "=" in item:
            key, value = item.split("=", 1)
            fields[key] = value
    return fields


def run_one(binary: Path, case_id: str, profile: dict, expected_label: str,
            timeout_seconds: int = 20) -> dict:
    # A kernel-assigned free loopback port, then a one-accept server in a fresh process.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server_argv = [str(binary), "server", str(port), str(CERT_EC), str(KEY_EC),
                   str(CERT_MLDSA), str(KEY_MLDSA)]
    client_argv = [str(binary), "client", str(port), profile["groups"],
                   profile["signature_algorithms"], str(CERT_EC if expected_label == "ECDSA-P-256" else CERT_MLDSA),
                   "ecdsa.localhost" if expected_label == "ECDSA-P-256" else "mldsa.localhost"]
    taskset = shutil.which("taskset")
    if taskset:
        server_argv = [taskset, "-c", "4", *server_argv]
        client_argv = [taskset, "-c", "2", *client_argv]
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(INSTALL / "lib") + (":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    env["OPENSSL_CONF"] = str(ROOT / "configs/openssl/feasibility-openssl.cnf")
    started = utc_now()
    server = subprocess.Popen(server_argv, cwd=ROOT, env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
    server_lines: list[str] = []
    try:
        ready_deadline = time.monotonic() + 5
        while time.monotonic() < ready_deadline:
            line = server.stdout.readline() if server.stdout else ""
            if line:
                server_lines.append(line.rstrip())
                if line.startswith("READY\t"):
                    break
            elif server.poll() is not None:
                break
        if not any(line.startswith("READY\t") for line in server_lines):
            server_out, server_err = server.communicate(timeout=5)
            if server_out:
                server_lines.extend(server_out.splitlines())
            return {"case_id": case_id, "client_profile": case_id,
                    "selected_server_credential_label": None, "expected_server_credential_label": expected_label,
                    "client": {"returncode": None, "stdout": "", "stderr": "server did not become ready"},
                    "server": {"returncode": server.returncode, "stdout": server_lines,
                               "stderr": server_err.strip()}, "started_utc": started, "ended_utc": utc_now()}
        client = subprocess.run(client_argv, cwd=ROOT, env=env, capture_output=True, text=True,
                                timeout=timeout_seconds)
        try:
            server_out, server_err = server.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            server.kill()
            server_out, server_err = server.communicate()
            server_err += "\nserver timeout"
        if server_out:
            server_lines.extend(server_out.splitlines())
        client_result_line = next((x for x in client.stdout.splitlines() if x.startswith("CLIENT_RESULT\t")), "")
        server_result_line = next((x for x in server_lines if x.startswith("SERVER_RESULT\t")), "")
        client_fields = parse_fields(client_result_line, "CLIENT_RESULT")
        server_fields = parse_fields(server_result_line, "SERVER_RESULT")
        actual_label = server_fields.get("selected_server_credential")
        expected_type = "EC" if expected_label == "ECDSA-P-256" else "ML-DSA-65"
        expected_signature = "ecdsa_secp256r1_sha256" if expected_label == "ECDSA-P-256" else "mldsa65"
        valid = (
            client.returncode == 0 and server.returncode == 0 and
            client_fields.get("tls_version") == "TLSv1.3" and
            client_fields.get("cipher") == "TLS_AES_128_GCM_SHA256" and
            client_fields.get("chain_result") == "PASS" and
            client_fields.get("hostname_result") == "PASS" and
            client_fields.get("peer_public_key_type") == expected_type and
            client_fields.get("certificate_verify_signature_scheme") == expected_signature and
            actual_label == expected_label and
            server_fields.get("tls_version") == "TLSv1.3" and
            server_fields.get("cipher") == "TLS_AES_128_GCM_SHA256" and
            bool(client_fields.get("group")) and client_fields.get("group") != "(unknown)"
        )
        return {
            "case_id": case_id, "client_profile": case_id,
            "configured_groups": profile["groups"],
            "configured_signature_algorithms": profile["signature_algorithms"],
            "selected_server_credential_label": actual_label,
            "expected_server_credential_label": expected_label,
            "expected_peer_public_key_type": expected_type,
            "expected_certificate_verify_signature_scheme": expected_signature,
            "client": {"argv": client_argv, "returncode": client.returncode,
                       "stdout": client.stdout.strip(), "stderr": client.stderr.strip(),
                       "observed": client_fields},
            "server": {"argv": server_argv, "returncode": server.returncode,
                       "stdout": server_lines, "stderr": server_err.strip(),
                       "observed": server_fields},
            "success": bool(valid), "started_utc": started, "ended_utc": utc_now(),
        }
    except (OSError, subprocess.SubprocessError) as exc:
        if server.poll() is None:
            server.kill()
        out, err = server.communicate()
        if out:
            server_lines.extend(out.splitlines())
        return {"case_id": case_id, "client_profile": case_id,
                "selected_server_credential_label": None,
                "expected_server_credential_label": expected_label,
                "client": {"returncode": None, "stdout": "", "stderr": str(exc)},
                "server": {"returncode": server.returncode, "stdout": server_lines,
                           "stderr": err.strip()}, "success": False,
                "started_utc": started, "ended_utc": utc_now()}


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text())
    campaign_id = "compat-v1-gate-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    evidence_dir = ROOT / "data/compatibility/v1/gate" / campaign_id
    evidence_dir.mkdir(parents=True, exist_ok=False)
    base_commit = EXPECTED_REPO_COMMIT
    historical_before = base_manifest(base_commit)
    evidence = {
        "schema_version": 1,
        "study": "Follow-up Study A",
        "protocol_path": "docs/phase-4/PROFILE_COMPATIBILITY_PROTOCOL.md",
        "workflow_version": "v1",
        "campaign_id": campaign_id,
        "status": "in_progress",
        "purpose": "mandatory dual-certificate capability gate only; no compatibility matrix attempted",
        "started_utc": utc_now(),
        "repository": {"path": str(ROOT), "commit_before_gate": base_commit,
                       "branch": cmd(["git", "branch", "--show-current"])["stdout"]},
        "openssl": {"install_path": str(INSTALL), "version": cmd([str(INSTALL / "bin/openssl"), "version", "-a"]),
                    "source_path": str(OPENSSL_SOURCE),
                    "source_commit": cmd(["git", "-C", str(OPENSSL_SOURCE), "rev-parse", "HEAD"])["stdout"]},
        "environment_snapshot": environment_snapshot(),
        "profile_configuration": config,
        "profile_configuration_sha256": sha256(CONFIG_PATH),
        "harness_source_sha256": sha256(SOURCE_PATH),
        "historical_tracked_files_before_sha256": historical_before,
        "test_results": [],
    }
    failures = []
    if evidence["openssl"]["source_commit"] != EXPECTED_OPENSSL_COMMIT:
        failures.append("pinned OpenSSL source commit mismatch")
    if evidence["openssl"]["version"].get("returncode") != 0 or "OpenSSL 3.5.9" not in evidence["openssl"]["version"].get("stdout", ""):
        failures.append("pinned OpenSSL 3.5.9 installation unavailable")
    for item in (CERT_EC, KEY_EC, CERT_MLDSA, KEY_MLDSA):
        if not item.is_file():
            failures.append(f"required ignored local credential missing: {item.name}")

    binary = evidence_dir / "tls_compat_gate"
    compiler = shutil.which(os.environ.get("CC", "cc"))
    compile_result = {"returncode": None, "argv": [], "stdout": "", "stderr": "compiler unavailable"}
    if compiler:
        compile_argv = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-I", str(INSTALL / "include"), str(SOURCE_PATH),
                        "-L", str(INSTALL / "lib"), f"-Wl,-rpath,{INSTALL / 'lib'}",
                        "-lssl", "-lcrypto", "-o", str(binary)]
        compile_result = cmd(compile_argv, timeout=90)
    evidence["build"] = {**compile_result,
                          "binary_sha256": sha256(binary) if binary.is_file() else None,
                          "linked_openssl": cmd(["ldd", str(binary)]) if binary.is_file() else None}
    if compile_result.get("returncode") != 0:
        failures.append("native dual-certificate harness compilation failed")

    if not failures:
        for case_id, expected_label in (("L", "ECDSA-P-256"), ("D", "ML-DSA-65")):
            result = run_one(binary, case_id, config["profiles"][case_id], expected_label)
            evidence["test_results"].append(result)
            if not result.get("success"):
                failures.append(f"gate test {case_id} failed or selected unexpected credential")
    evidence["ended_utc"] = utc_now()
    evidence["gate_passed"] = not failures and len(evidence["test_results"]) == 2
    evidence["failures"] = failures
    evidence["matrix_started"] = False
    evidence["matrix_attempt_count"] = 0
    historical_after = base_manifest(base_commit)
    changed = sorted(path for path, digest in historical_before.items()
                     if historical_after.get(path) != digest)
    evidence["historical_tracked_files_after_sha256"] = historical_after
    evidence["historical_tracked_files_unchanged"] = historical_before == historical_after
    evidence["historical_changed_paths"] = changed
    evidence["status"] = "gate_passed_matrix_not_run" if evidence["gate_passed"] else "gate_failed_matrix_not_run"
    if binary.exists():
        binary.unlink()
    evidence_path = evidence_dir / "gate-evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (evidence_dir / "gate-evidence.json.sha256").write_text(f"{sha256(evidence_path)}  gate-evidence.json\n")
    print(json.dumps({"campaign_id": campaign_id, "gate_passed": evidence["gate_passed"],
                      "test_results": [{"case_id": r.get("case_id"), "success": r.get("success"),
                                       "selected_server_credential_label": r.get("selected_server_credential_label"),
                                       "observed": r.get("client", {}).get("observed", {})}
                                       for r in evidence["test_results"]],
                      "historical_tracked_files_unchanged": evidence["historical_tracked_files_unchanged"],
                      "historical_changed_paths": changed,
                      "evidence_path": str(evidence_path)}, indent=2))
    return 0 if evidence["gate_passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
