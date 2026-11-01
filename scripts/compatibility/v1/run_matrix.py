#!/usr/bin/env python3
"""Run the approved 48-attempt Follow-up Study A compatibility matrix once."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import random
import re
import secrets
import shutil
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "configs/compatibility/v1/profiles.json"
SOURCE_PATH = HERE / "tls_compat_matrix.c"
INSTALL = ROOT / "third_party/openssl-3.5.9/install"
OPENSSL_SOURCE = ROOT / "third_party/openssl-3.5.9/source"
EXPECTED_OPENSSL_COMMIT = "45e844fa2a14ec92d146bd8f5778ac130b6625fb"
CREDS = ROOT / "credentials/compat-v1"
CERT_EC = CREDS / "ecdsa.cert.pem"
KEY_EC = CREDS / "ecdsa.key.pem"
CERT_MLDSA = CREDS / "mldsa.cert.pem"
KEY_MLDSA = CREDS / "mldsa.key.pem"
CA_BUNDLE = CREDS / "combined-ca-bundle.pem"
EXPECTED_REPO_COMMIT = subprocess.run(
    ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
).stdout.strip()
EXPECTED_PROFILES = {
    "L": {"groups": "x25519", "signature_algorithms": "ecdsa_secp256r1_sha256",
          "server_credential_capability": ["ECDSA-P-256"]},
    "H": {"groups": "X25519MLKEM768:x25519", "signature_algorithms": "ecdsa_secp256r1_sha256",
          "server_credential_capability": ["ECDSA-P-256"]},
    "D": {"groups": "X25519MLKEM768:x25519:MLKEM768",
          "signature_algorithms": "ecdsa_secp256r1_sha256:mldsa65",
          "server_credential_capability": ["ECDSA-P-256", "ML-DSA-65"]},
    "Q": {"groups": "MLKEM768", "signature_algorithms": "mldsa65",
          "server_credential_capability": ["ML-DSA-65"]},
}
CSV_FIELDS = [
    "campaign_id", "attempt_id", "sequence_index", "repetition",
    "client_profile", "server_profile", "configured_client_groups",
    "configured_client_signature_algorithms", "configured_server_groups",
    "configured_server_signature_algorithms", "selected_server_credential_label",
    "client_return_code", "server_return_code", "success", "failure_category",
    "client_error_sanitized", "server_error_sanitized", "tls_version", "cipher",
    "negotiated_group", "peer_public_key_type", "certificate_verify_signature_scheme",
    "chain_result", "hostname_result", "client_started_utc", "attempt_ended_utc",
    "repository_commit", "openssl_source_commit", "openssl_executable_version",
    "openssl_library_version", "ecdsa_certificate_sha256", "mldsa_certificate_sha256",
    "ecdsa_trust_sha256", "mldsa_trust_sha256", "combined_trust_bundle_sha256",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd(args: list[str], *, env: dict[str, str] | None = None,
        timeout: int = 15) -> dict:
    try:
        result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True,
                                text=True, timeout=timeout)
        return {"argv": args, "returncode": result.returncode,
                "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except (OSError, subprocess.SubprocessError) as exc:
        return {"argv": args, "returncode": None, "stdout": "", "stderr": str(exc)}


def pinned_env() -> dict[str, str]:
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(INSTALL / "lib") + (
        ":" + env["LD_LIBRARY_PATH"] if env.get("LD_LIBRARY_PATH") else "")
    env["OPENSSL_CONF"] = str(ROOT / "configs/openssl/feasibility-openssl.cnf")
    return env


def openssl_identity() -> dict:
    executable = INSTALL / "bin/openssl"
    env = pinned_env()
    exe = cmd([str(executable), "version", "-v"], env=env)
    detail = cmd([str(executable), "version", "-a"], env=env)
    linked = cmd(["ldd", str(executable)], env=env)
    library_line = next((line.strip() for line in detail["stdout"].splitlines()
                         if "Library: OpenSSL " in line), "")
    exe_ok = bool(re.search(r"^OpenSSL 3\.5\.9(?:\s|$)", exe["stdout"]))
    lib_ok = bool(re.search(r"Library: OpenSSL 3\.5\.9(?:\s|$)", library_line))
    paths = {Path(path).name.split(".so", 1)[0]: path
             for path in re.findall(r"=>\s+(\S+)", linked["stdout"])
             if Path(path).name.startswith(("libssl.so", "libcrypto.so"))}
    expected = str(INSTALL / "lib") + "/"
    linked_ok = (linked["returncode"] == 0 and set(paths) == {"libssl", "libcrypto"}
                 and all(path.startswith(expected) for path in paths.values()))
    return {"executable_path": str(executable), "executable_version": exe,
            "library_version": {"reported_line": library_line,
                                "returncode": detail["returncode"], "stderr": detail["stderr"]},
            "ldd": linked, "executable_is_3_5_9": exe_ok, "library_is_3_5_9": lib_ok,
            "pinned_libssl_libcrypto_linkage": linked_ok,
            "guard_passed": exe_ok and lib_ok and linked_ok}


def cpu_list() -> list[int]:
    text = Path("/sys/devices/system/cpu/online").read_text().strip()
    output: list[int] = []
    for item in text.split(","):
        bound = [int(x) for x in item.split("-")]
        output.extend(range(bound[0], bound[-1] + 1))
    return output


def environment_snapshot() -> dict:
    topology = {}
    frequencies = {}
    for cpu in cpu_list():
        base = Path(f"/sys/devices/system/cpu/cpu{cpu}")
        def read(path: Path):
            try:
                return path.read_text().strip()
            except OSError:
                return None
        topology[str(cpu)] = {
            "online": read(base / "online") if cpu else "1",
            "thread_siblings_list": read(base / "topology/thread_siblings_list"),
            "core_id": read(base / "topology/core_id"),
            "physical_package_id": read(base / "topology/physical_package_id"),
        }
        frequencies[str(cpu)] = read(base / "cpufreq/scaling_cur_freq")
    policies = {}
    for path in sorted(Path("/sys/devices/system/cpu/cpufreq").glob("policy*")):
        policies[path.name] = {
            key: (path / key).read_text().strip() if (path / key).exists() else None
            for key in ("related_cpus", "scaling_governor", "energy_performance_preference",
                        "scaling_min_freq", "scaling_max_freq", "scaling_cur_freq")}
    supplies = {}
    for path in sorted(Path("/sys/class/power_supply").glob("*")):
        values = {key: (path / key).read_text().strip()
                  for key in ("type", "online", "status", "capacity")
                  if (path / key).exists()}
        if values:
            supplies[path.name] = values
    thermal = {}
    for path in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        try:
            raw = int((path / "temp").read_text().strip())
            thermal[path.name] = {"type": (path / "type").read_text().strip(), "temp_c": raw / 1000}
        except (OSError, ValueError):
            continue
    try:
        processes = subprocess.run(["ps", "-eo", "comm=,%cpu=", "--sort=-%cpu"],
                                   capture_output=True, text=True, timeout=5, check=True).stdout.splitlines()[:20]
    except (OSError, subprocess.SubprocessError):
        processes = []
    try:
        load = list(os.getloadavg())
    except OSError:
        load = None
    try:
        power_profile = subprocess.run(["powerprofilesctl", "get"], capture_output=True,
                                       text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        power_profile = None
    return {
        "captured_utc": utc_now(), "platform": platform.platform(),
        "uname": platform.uname()._asdict(), "ac_battery": supplies,
        "power_profile_observed_no_guard": power_profile,
        "platform_profile_observed_no_guard": (Path("/sys/firmware/acpi/platform_profile").read_text().strip()
                                               if Path("/sys/firmware/acpi/platform_profile").exists() else None),
        "cpu_topology": topology, "cpu_frequencies_khz": frequencies,
        "cpu_policies_observed_no_guard": policies, "thermal_zones": thermal,
        "load_average_1_5_15": load, "top_running_process_summary": processes,
        "note": "environment recorded for functional-study context; no performance-mode guard or power change applied",
    }


def cert_metadata(cert_path: Path, expected_host: str, expected_key: str,
                  timestamp: datetime) -> dict:
    env = pinned_env()
    openssl = str(INSTALL / "bin/openssl")
    desc = subprocess.run([openssl, "x509", "-in", str(cert_path), "-noout", "-subject",
                           "-nameopt", "RFC2253", "-dates", "-ext", "subjectAltName"],
                          cwd=ROOT, env=env, capture_output=True, text=True)
    keydesc = subprocess.run([openssl, "x509", "-in", str(cert_path), "-noout", "-text"],
                             cwd=ROOT, env=env, capture_output=True, text=True)
    subject = re.search(r"^subject=(.*)$", desc.stdout, re.M)
    before = re.search(r"^notBefore=(.*)$", desc.stdout, re.M)
    after = re.search(r"^notAfter=(.*)$", desc.stdout, re.M)
    san = re.search(r"X509v3 Subject Alternative Name:\s*\n\s*([^\n]+)", desc.stdout)
    keytype = re.search(r"Public Key Algorithm:\s*(.+)", keydesc.stdout)
    curve = re.search(r"ASN1 OID:\s*(.+)", keydesc.stdout)
    errors: list[str] = []
    parsed = []
    for match, label in ((before, "notBefore"), (after, "notAfter")):
        if not match:
            errors.append(f"missing {label}"); parsed.append(None); continue
        try:
            parsed.append(datetime.strptime(match.group(1).strip(), "%b %d %H:%M:%S %Y GMT").replace(tzinfo=timezone.utc))
        except ValueError as exc:
            errors.append(f"invalid {label}: {exc}"); parsed.append(None)
    not_before, not_after = parsed
    sans = [x.strip() for x in san.group(1).split(",")] if san else []
    observed_key = keytype.group(1).strip() if keytype else None
    observed_curve = curve.group(1).strip() if curve else None
    current = bool(not_before and not_after and not_before <= timestamp <= not_after)
    days = (not_after - not_before).total_seconds() / 86400 if not_before and not_after else None
    checks = {
        "readable": desc.returncode == 0 and keydesc.returncode == 0,
        "expected_san_hostname": f"DNS:{expected_host}" in sans,
        "expected_public_key_type": observed_key == expected_key,
        "expected_curve": expected_key != "id-ecPublicKey" or observed_curve == "prime256v1",
        "valid_at_preflight_timestamp": current,
        "validity_at_least_365_days": days is not None and days >= 365,
    }
    return {"path": str(cert_path), "sha256": sha256(cert_path) if cert_path.is_file() else None,
            "subject": subject.group(1).strip() if subject else None,
            "san_dns_entries": sans, "expected_hostname": expected_host,
            "public_key_type": observed_key, "curve": observed_curve,
            "expected_public_key_type": expected_key,
            "not_before_utc": not_before.isoformat().replace("+00:00", "Z") if not_before else None,
            "not_after_utc": not_after.isoformat().replace("+00:00", "Z") if not_after else None,
            "validity_days": days,
            "evaluated_at_utc": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "checks": checks, "passed": all(checks.values()) and not errors,
            "parse_errors": errors, "openssl_stderr": "\n".join(x for x in (desc.stderr.strip(), keydesc.stderr.strip()) if x)}


def historical_manifest(commit: str) -> dict[str, str]:
    tracked = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.splitlines()
    result = {}
    for name in tracked:
        path = ROOT / name
        if path.is_file():
            result[name] = sha256(path)
    return result


def sanitize(text: str) -> str:
    value = text.replace(str(ROOT), "<repo>").replace(str(CREDS), "<compat-credentials>")
    value = re.sub(r"0x[0-9a-fA-F]+", "<address>", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:1500]


def parse_fields(line: str, prefix: str) -> dict[str, str]:
    output = {}
    if not line.startswith(prefix + "\t"):
        return output
    for part in line.split("\t")[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            output[key] = value
    return output


def expected_label(client_id: str, server_id: str) -> str:
    if server_id == "D":
        return "ML-DSA-65" if client_id in {"D", "Q"} else "ECDSA-P-256"
    return EXPECTED_PROFILES[server_id]["server_credential_capability"][0]


def classify_failure(client_result: dict, client_error: str, server_error: str,
                     client_rc: int | None, server_rc: int | None) -> str:
    if client_result.get("chain_result") == "FAIL" or client_result.get("hostname_result") == "FAIL":
        return "CERTIFICATE_OR_HOSTNAME_VERIFICATION_FAILED"
    combined = f"{client_error} {server_error}".lower()
    if any(term in combined for term in ("no shared group", "no suitable groups", "no groups in common", "no suitable key share")):
        return "NO_COMMON_GROUP"
    if any(term in combined for term in ("no suitable signature", "no supported client signature", "signature_algorithms")):
        return "NO_COMMON_SIGNATURE_CAPABILITY"
    if "certificate" in combined or "unknown ca" in combined:
        return "CERTIFICATE_NEGOTIATION_OR_VERIFICATION_FAILED"
    if client_rc is None or server_rc is None:
        return "PROCESS_OR_TIMEOUT_FAILURE"
    return "TLS_HANDSHAKE_FAILED"


def run_attempt(binary: Path, campaign_id: str, sequence: int,
                repetition: int, client_id: str, server_id: str,
                config: dict, identity: dict, source_commit: str,
                certs: dict, trust_hashes: dict) -> dict:
    started = utc_now()
    profile_client = config["profiles"][client_id]
    profile_server = config["profiles"][server_id]
    label_expected = expected_label(client_id, server_id)
    client_ca = {"L": CERT_EC, "H": CERT_EC, "D": CA_BUNDLE, "Q": CERT_MLDSA}[client_id]
    server_hostname = "ecdsa.localhost" if label_expected == "ECDSA-P-256" else "mldsa.localhost"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server_argv = [str(binary), "server", str(port), server_id,
                   profile_server["groups"], profile_server["signature_algorithms"],
                   str(CERT_EC), str(KEY_EC), str(CERT_MLDSA), str(KEY_MLDSA)]
    client_argv = [str(binary), "client", str(port), client_id,
                   profile_client["groups"], profile_client["signature_algorithms"],
                   str(client_ca), server_hostname]
    env = pinned_env()
    server_proc = None
    server_stdout = ""
    server_stderr = ""
    client_stdout = ""
    client_stderr = ""
    client_rc = None
    server_rc = None
    try:
        server_proc = subprocess.Popen(server_argv, cwd=ROOT, env=env, text=True,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
        ready_lines: list[str] = []
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            line = server_proc.stdout.readline() if server_proc.stdout else ""
            if line:
                ready_lines.append(line.rstrip())
                if line.startswith("READY\t"):
                    break
            elif server_proc.poll() is not None:
                break
        if not any(x.startswith("READY\t") for x in ready_lines):
            out, err = server_proc.communicate(timeout=5)
            server_rc = server_proc.returncode
            server_stdout = "\n".join(ready_lines + out.splitlines())
            server_stderr = err
            client_stderr = "server did not become ready"
        else:
            client_proc = subprocess.run(client_argv, cwd=ROOT, env=env, capture_output=True,
                                         text=True, timeout=20)
            client_rc = client_proc.returncode
            client_stdout = client_proc.stdout
            client_stderr = client_proc.stderr
            try:
                out, err = server_proc.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                out, err = server_proc.communicate()
                err += "\nserver timeout"
            server_rc = server_proc.returncode
            server_stdout = "\n".join(ready_lines + out.splitlines())
            server_stderr = err
    except (OSError, subprocess.SubprocessError) as exc:
        client_stderr = str(exc)
        if server_proc is not None:
            if server_proc.poll() is None:
                server_proc.kill()
            out, err = server_proc.communicate()
            server_rc = server_proc.returncode
            server_stdout = out
            server_stderr = err
    client_err_safe = sanitize(client_stderr)
    server_err_safe = sanitize(server_stderr)
    client_line = next((line for line in client_stdout.splitlines()
                        if line.startswith("CLIENT_RESULT\t")), "")
    server_lines = server_stdout.splitlines()
    server_line = next((line for line in server_lines
                        if line.startswith("SERVER_RESULT\t")), "")
    server_fail_line = next((line for line in server_lines
                             if line.startswith("SERVER_FAILURE\t")), "")
    client_fields = parse_fields(client_line, "CLIENT_RESULT")
    server_fields = parse_fields(server_line, "SERVER_RESULT") or parse_fields(server_fail_line, "SERVER_FAILURE")
    passed = (client_fields.get("handshake") == "PASS" and
              client_fields.get("chain_result") == "PASS" and
              client_fields.get("hostname_result") == "PASS")
    category = "NONE" if passed else classify_failure(client_fields, client_err_safe,
                                                       server_err_safe, client_rc, server_rc)
    row = {
        "campaign_id": campaign_id,
        "attempt_id": f"{campaign_id}-a{sequence:02d}-{uuid.uuid4().hex[:8]}",
        "sequence_index": sequence, "repetition": repetition,
        "client_profile": client_id, "server_profile": server_id,
        "configured_client_groups": profile_client["groups"],
        "configured_client_signature_algorithms": profile_client["signature_algorithms"],
        "configured_server_groups": profile_server["groups"],
        "configured_server_signature_algorithms": profile_server["signature_algorithms"],
        "selected_server_credential_label": server_fields.get("selected_server_credential"),
        "client_return_code": client_rc, "server_return_code": server_rc,
        "success": passed, "failure_category": category,
        "client_error_sanitized": client_err_safe,
        "server_error_sanitized": server_err_safe,
        "tls_version": client_fields.get("tls_version"),
        "cipher": client_fields.get("cipher"),
        "negotiated_group": client_fields.get("group"),
        "peer_public_key_type": client_fields.get("peer_public_key_type"),
        "certificate_verify_signature_scheme": client_fields.get("certificate_verify_signature_scheme"),
        "chain_result": client_fields.get("chain_result"),
        "hostname_result": client_fields.get("hostname_result"),
        "client_started_utc": started, "attempt_ended_utc": utc_now(),
        "repository_commit": EXPECTED_REPO_COMMIT,
        "openssl_source_commit": source_commit,
        "openssl_executable_version": identity["executable_version"]["stdout"],
        "openssl_library_version": identity["library_version"]["reported_line"],
        "ecdsa_certificate_sha256": certs["ecdsa"]["sha256"],
        "mldsa_certificate_sha256": certs["mldsa"]["sha256"],
        "ecdsa_trust_sha256": trust_hashes["ecdsa"],
        "mldsa_trust_sha256": trust_hashes["mldsa"],
        "combined_trust_bundle_sha256": trust_hashes["combined"],
    }
    row["_process_detail"] = {
        "client_argv": client_argv, "server_argv": server_argv,
        "client_stdout": client_stdout.strip(), "server_stdout": server_lines,
        "client_result_fields": client_fields, "server_result_fields": server_fields,
        "server_result_emitted_after_ssl_accept": bool(server_line and server_rc == 0),
        "expected_server_credential_by_capability": label_expected,
    }
    return row


def failure_category_for_report(row: dict) -> str:
    return row["failure_category"]


def write_report(path: Path, campaign_id: str, rows: list[dict],
                 seed: int, repo_commit: str) -> None:
    lines = [
        "# Follow-up Study A compatibility matrix outcome",
        "",
        f"Campaign: `{campaign_id}`",
        f"Repository commit: `{repo_commit}`",
        f"Recorded master seed: `{seed}`",
        "",
        "This is local native-OpenSSL compatibility evidence with ignored local test credentials. It is not browser, public-PKI, Internet, or production interoperability evidence. No performance measurements or comparisons were made.",
        "",
        "## All ordered-pair outcomes",
        "",
        "Each cell lists repetitions 1, 2, and 3 in parentheses. Successful entries give selected credential and observed TLS parameters. Failed entries give their recorded failure category.",
        "",
        "| Client \\ Server | L | H | D | Q |",
        "| --- | --- | --- | --- | --- |",
    ]
    for client_id in ("L", "H", "D", "Q"):
        cell_values = []
        for server_id in ("L", "H", "D", "Q"):
            cell = sorted((row for row in rows
                           if row["client_profile"] == client_id and row["server_profile"] == server_id),
                          key=lambda item: item["repetition"])
            rendered = []
            for item in cell:
                if item["success"]:
                    rendered.append(
                        f"r{item['repetition']}: PASS, {item['selected_server_credential_label']}, "
                        f"{item['tls_version']}/{item['cipher']}/{item['negotiated_group']}, "
                        f"{item['peer_public_key_type']}, {item['certificate_verify_signature_scheme']}, "
                        f"chain+host PASS")
                else:
                    rendered.append(f"r{item['repetition']}: FAIL ({failure_category_for_report(item)})")
            cell_values.append("<br>".join(rendered) if len(rendered) == 3 else "INCOMPLETE: " + "; ".join(rendered))
        lines.append("| " + client_id + " | " + " | ".join(cell_values) + " |")
    lines += [
        "",
        "## Attempt records",
        "",
        "Full per-attempt configured profile lists, return codes, sanitized errors, verification fields, timestamps, identities, and credential hashes are in `attempts.csv`. The actual negotiated group is recorded as observed; no presumed group was a pass condition.",
        "",
        f"Total attempts: {len(rows)}; successful: {sum(bool(x['success']) for x in rows)}; failed: {sum(not x['success'] for x in rows)}.",
        "",
        "No failed attempt was retried. The schedule contains 48 unique fresh-process attempts (16 ordered pairs × 3 repetitions).",
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text())
    if set(config.get("profiles", {})) != {"L", "H", "D", "Q"}:
        raise SystemExit("configuration guard failed: expected profiles L/H/D/Q")
    config_mismatches = []
    for profile_id, expected in EXPECTED_PROFILES.items():
        observed = config["profiles"][profile_id]
        for key, expected_value in expected.items():
            if observed.get(key) != expected_value:
                config_mismatches.append(f"profile {profile_id} {key} differs from approved protocol")
    campaign_id = "compat-v1-matrix-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    source_clean = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                  capture_output=True, text=True, check=True).stdout.strip() == ""
    out_dir = ROOT / "data/compatibility/v1/matrix" / campaign_id
    out_dir.mkdir(parents=True, exist_ok=False)
    started = utc_now()
    base_commit = EXPECTED_REPO_COMMIT
    hist_before = historical_manifest(base_commit)
    preflight_time = datetime.now(timezone.utc)
    identity = openssl_identity()
    source_commit = cmd(["git", "-C", str(OPENSSL_SOURCE), "rev-parse", "HEAD"])["stdout"]
    certs = {
        "ecdsa": cert_metadata(CERT_EC, "ecdsa.localhost", "id-ecPublicKey", preflight_time)
        if CERT_EC.is_file() else {"passed": False, "sha256": None, "checks": {}, "parse_errors": ["missing"]},
        "mldsa": cert_metadata(CERT_MLDSA, "mldsa.localhost", "ML-DSA-65", preflight_time)
        if CERT_MLDSA.is_file() else {"passed": False, "sha256": None, "checks": {}, "parse_errors": ["missing"]},
    }
    trust_hashes = {}
    trust_bundle_bytes = CERT_EC.read_bytes().rstrip() + b"\n" + CERT_MLDSA.read_bytes().rstrip() + b"\n" if CERT_EC.is_file() and CERT_MLDSA.is_file() else b""
    trust_hashes = {
        "ecdsa": sha256(CERT_EC) if CERT_EC.is_file() else None,
        "mldsa": sha256(CERT_MLDSA) if CERT_MLDSA.is_file() else None,
        "combined": sha256(CA_BUNDLE) if CA_BUNDLE.is_file() else None,
    }
    ignore_results = {str(path): subprocess.run(["git", "check-ignore", "-q", str(path)], cwd=ROOT).returncode == 0
                      for path in (CERT_EC, KEY_EC, CERT_MLDSA, KEY_MLDSA, CA_BUNDLE)}
    trust_valid = CA_BUNDLE.is_file() and CA_BUNDLE.read_bytes() == trust_bundle_bytes
    source_commit_ok = source_commit == EXPECTED_OPENSSL_COMMIT
    preflight_failures = []
    preflight_failures.extend(config_mismatches)
    if not identity["guard_passed"]: preflight_failures.append("OpenSSL executable/library/linkage guard failed")
    if not source_commit_ok: preflight_failures.append("pinned OpenSSL source commit mismatch")
    if not source_clean: preflight_failures.append("repository has uncommitted changes before matrix run")
    for name, item in certs.items():
        if not item.get("passed"): preflight_failures.append(f"{name} certificate preflight failed")
    for path in (CERT_EC, KEY_EC, CERT_MLDSA, KEY_MLDSA, CA_BUNDLE):
        if not path.is_file(): preflight_failures.append(f"required local compatibility credential/trust file missing: {path.name}")
        if not ignore_results[str(path)]: preflight_failures.append(f"credential/trust file is not ignored: {path.name}")
    if not trust_valid: preflight_failures.append("combined trust bundle does not exactly contain the two compatibility roots")

    seed = secrets.randbits(64)
    schedule = [(client_id, server_id, repetition)
                for client_id in ("L", "H", "D", "Q")
                for server_id in ("L", "H", "D", "Q")
                for repetition in (1, 2, 3)]
    random.Random(seed).shuffle(schedule)
    compiler = shutil.which(os.environ.get("CC", "cc"))
    binary = out_dir / "tls_compat_matrix"
    compile_result = {"returncode": None, "argv": [], "stdout": "", "stderr": "compiler unavailable"}
    if compiler:
        compile_argv = [compiler, "-std=c11", "-O2", "-Wall", "-Wextra", "-Werror",
                        "-I", str(INSTALL / "include"), str(SOURCE_PATH),
                        "-L", str(INSTALL / "lib"), f"-Wl,-rpath,{INSTALL / 'lib'}",
                        "-lssl", "-lcrypto", "-o", str(binary)]
        compile_result = cmd(compile_argv, timeout=90)
    compile_result["binary_sha256"] = sha256(binary) if binary.is_file() else None
    compile_result["ldd"] = cmd(["ldd", str(binary)]) if binary.is_file() else None
    if compile_result.get("returncode") != 0: preflight_failures.append("matrix harness compile failed")
    if compile_result.get("ldd") and ("libssl.so.3 => " + str(INSTALL / "lib/libssl.so.3") not in compile_result["ldd"]["stdout"] or
                                      "libcrypto.so.3 => " + str(INSTALL / "lib/libcrypto.so.3") not in compile_result["ldd"]["stdout"]):
        preflight_failures.append("matrix harness linked libraries are not the pinned installation")

    environment_before = environment_snapshot()
    preflight = {
        "checked_at_utc": utc_now(), "passed": not preflight_failures,
        "failures": preflight_failures, "openssl_identity": identity,
        "openssl_source_commit": source_commit, "openssl_source_commit_expected": EXPECTED_OPENSSL_COMMIT,
        "certificates": certs, "trust_hashes": trust_hashes,
        "trust_bundle_matches_roots": trust_valid, "ignore_results": ignore_results,
        "compile": compile_result, "environment_snapshot": environment_before,
        "repository_clean_before_run": source_clean,
    }
    if preflight_failures:
        meta = {"schema_version": 1, "campaign_id": campaign_id, "status": "preflight_failed_no_attempts",
                "started_utc": started, "ended_utc": utc_now(), "repository_commit": base_commit,
                "profile_configuration": config, "preflight": preflight,
                "matrix_attempt_count": 0, "matrix_started": False,
                "historical_tracked_files_before_sha256": hist_before}
        (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
        return 1

    rows = []
    planned_order = []
    for index, (client_id, server_id, repetition) in enumerate(schedule, 1):
        planned_order.append({"sequence_index": index, "client_profile": client_id,
                              "server_profile": server_id, "repetition": repetition})
        rows.append(run_attempt(binary, campaign_id, index, repetition, client_id, server_id,
                                config, identity, source_commit, certs, trust_hashes))
    environment_after = environment_snapshot()
    hist_after = historical_manifest(base_commit)
    history_same = hist_before == hist_after
    for row in rows:
        row.pop("_process_detail", None)
    csv_path = out_dir / "attempts.csv"
    with csv_path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    report_path = out_dir / "outcome-report.md"
    write_report(report_path, campaign_id, rows, seed, base_commit)
    meta = {
        "schema_version": 1, "study": "Follow-up Study A",
        "scope": "local native-OpenSSL functional profile compatibility only",
        "limitations": ["not browser evidence", "not public-PKI evidence", "not Internet evidence", "not production interoperability evidence"],
        "campaign_id": campaign_id, "status": "complete" if len(rows) == 48 else "incomplete",
        "started_utc": started, "ended_utc": utc_now(),
        "repository": {"path": str(ROOT), "branch": cmd(["git", "branch", "--show-current"])["stdout"], "commit": base_commit},
        "openssl_identity": identity, "openssl_source_commit": source_commit,
        "profile_configuration": config,
        "profile_configuration_sha256": sha256(CONFIG_PATH),
        "harness_source_sha256": sha256(SOURCE_PATH),
        "credentials": {"directory": str(CREDS), "certificates": certs,
                        "trust_hashes": trust_hashes, "keys_and_certs_ignored": ignore_results},
        "preflight": preflight,
        "environment_before": environment_before, "environment_after": environment_after,
        "master_seed": seed, "randomization": "Python random.Random(master_seed).shuffle over 16 ordered pairs × 3 repetitions",
        "planned_and_realized_order": planned_order,
        "attempt_count": len(rows), "successful_attempts": sum(bool(row["success"]) for row in rows),
        "failed_attempts": sum(not row["success"] for row in rows),
        "failed_attempts_retried": False, "matrix_attempt_count": len(rows),
        "matrix_started": True, "historical_tracked_files_before_sha256": hist_before,
        "historical_tracked_files_after_sha256": hist_after,
        "historical_tracked_files_unchanged": history_same,
        "historical_changed_paths": sorted(key for key in set(hist_before) | set(hist_after)
                                            if hist_before.get(key) != hist_after.get(key)),
        "measurement_scope_note": "No latency, CPU, bytes, packets, or performance comparisons measured or reported.",
    }
    metadata_path = out_dir / "metadata.json"
    metadata_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    integrity = {
        "campaign_id": campaign_id,
        "files": {p.name: sha256(p) for p in (csv_path, metadata_path, report_path)},
        "historical_manifest_unchanged": history_same,
        "historical_changed_paths": meta["historical_changed_paths"],
        "matrix_attempt_count": len(rows),
    }
    integrity_path = out_dir / "integrity.json"
    integrity_path.write_text(json.dumps(integrity, indent=2, sort_keys=True) + "\n")
    (out_dir / "integrity.json.sha256").write_text(f"{sha256(integrity_path)}  integrity.json\n")
    if binary.exists(): binary.unlink()
    summary = {
        "campaign_id": campaign_id, "status": meta["status"],
        "attempt_count": len(rows), "successful_attempts": meta["successful_attempts"],
        "failed_attempts": meta["failed_attempts"], "matrix_attempt_count": len(rows),
        "historical_tracked_files_unchanged": history_same,
        "historical_changed_paths": meta["historical_changed_paths"],
        "output_dir": str(out_dir), "integrity": integrity,
    }
    print(json.dumps(summary, indent=2))
    return 0 if len(rows) == 48 else 1


if __name__ == "__main__":
    sys.exit(main())
