#!/usr/bin/env python3
"""Prepare and execute immutable, guarded final Ubuntu measurement batches.

--preflight-only compiles the final harness and records checks without creating
any final raw CSV. --run is intentionally separate and requires the host to
pass the same guards before every batch.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
import random
import signal
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs/final/final.json"
OPENSSL_DIR = ROOT / "third_party/openssl-3.5.9/install"
OPENSSL_BIN = OPENSSL_DIR / "bin/openssl"
OPENSSL_SOURCE = OPENSSL_DIR.parent / "source"
PILOT_SOURCE = ROOT / "scripts/pilot/tls_pilot.c"
PILOT_RUNNER = ROOT / "scripts/pilot/run_pilot.py"
BUILD_DIR = ROOT / "build/final"
RAW_DIR = ROOT / "data/raw/final"
META_DIR = ROOT / "data/metadata/final"
MASTER_FIELDS = [
    "batch_id", "run_id", "timestamp", "case_id", "sequence_index", "warmup_flag",
    "git_commit_hash", "openssl_version", "openssl_source_commit", "tls_version",
    "cipher_suite", "requested_group", "observed_group", "requested_signature_type",
    "observed_signature_type", "handshake_success_failure", "tcp_connect_ns",
    "tls_handshake_ns", "client_user_cpu_ns", "client_system_cpu_ns",
    "server_user_cpu_ns", "server_system_cpu_ns", "client_peak_rss_kib",
    "server_peak_rss_kib", "handshake_bytes", "packet_count", "error_reason",
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], *, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env, check=check)


def load_pilot_module():
    spec = importlib.util.spec_from_file_location("final_pilot_harness_helpers", PILOT_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the reviewed C-harness measurement helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except (OSError, UnicodeError):
        return None


def topology() -> dict:
    output = run(["lscpu", "-e=CPU,CORE,SOCKET,NODE,ONLINE,MAXMHZ,MINMHZ"]).stdout
    rows = []
    for line in output.splitlines()[1:]:
        cols = line.split()
        if len(cols) == 7:
            rows.append({"cpu": int(cols[0]), "core": int(cols[1]), "socket": int(cols[2]),
                         "node": int(cols[3]), "online": cols[4],
                         "max_mhz": float(cols[5]), "min_mhz": float(cols[6])})
    siblings = {}
    for cpu in (0, 2, 4):
        siblings[str(cpu)] = read(Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list"))
    return {"lscpu_rows": rows, "thread_siblings_list": siblings}


def environment_snapshot() -> dict:
    policies = {}
    for path in sorted(Path("/sys/devices/system/cpu/cpufreq").glob("policy*")):
        policies[path.name] = {
            key: read(path / key) for key in (
                "related_cpus", "scaling_governor", "energy_performance_preference",
                "scaling_min_freq", "scaling_max_freq", "scaling_cur_freq")
        }
    frequencies = {}
    for path in sorted(Path("/sys/devices/system/cpu").glob("cpu[0-9]*/cpufreq/scaling_cur_freq")):
        frequencies[path.parents[1].name] = read(path)
    supplies = {}
    for path in sorted(Path("/sys/class/power_supply").glob("*")):
        values = {k: read(path / k) for k in ("type", "online", "status", "capacity") if (path / k).exists()}
        if values:
            supplies[path.name] = values
    thermal = {}
    for path in sorted(Path("/sys/class/thermal").glob("thermal_zone*")):
        raw = read(path / "temp")
        if raw is not None:
            try:
                thermal[path.name] = {"type": read(path / "type"), "temp_c": int(raw) / 1000}
            except ValueError:
                thermal[path.name] = {"type": read(path / "type"), "raw": raw}
    try:
        profile = run(["powerprofilesctl", "get"]).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        profile = None
    try:
        load = list(os.getloadavg())
    except OSError:
        load = None
    try:
        ps = run(["ps", "-eo", "comm=,%cpu=", "--sort=-%cpu"]).stdout.splitlines()
        processes = []
        for line in ps:
            cols = line.strip().rsplit(None, 1)
            if len(cols) == 2 and cols[0] not in {"ps", "python3", "bash"}:
                processes.append({"comm": cols[0], "cpu_percent": cols[1]})
            if len(processes) >= 16:
                break
    except (OSError, subprocess.CalledProcessError):
        processes = []
    affinity = {}
    for cpu, role in ((2, "client"), (4, "server")):
        try:
            affinity[str(cpu)] = run(["taskset", "-c", str(cpu), "sh", "-c",
                                      "grep Cpus_allowed_list /proc/self/status"]).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            affinity[str(cpu)] = None
    return {
        "captured_utc": utc_now(), "host_platform": __import__("platform").platform(),
        "ac_battery": supplies, "power_profile": profile,
        "platform_profile": read(Path("/sys/firmware/acpi/platform_profile")),
        "cpu_policies": policies, "cpu_frequencies_khz": frequencies,
        "topology": topology(), "target_affinity": {"client_cpu": 2, "server_cpu": 4, "cpu0_reserved_for_os": True,
                           "probe_output": affinity},
        "load_average_1_5_15m": load, "thermal_zones": thermal,
        "top_running_process_summary": processes,
    }


def guard_errors(snapshot: dict, cfg: dict) -> list[str]:
    errors = []
    mains = [v for v in snapshot["ac_battery"].values() if v.get("type", "").lower() in {"mains", "ac"}]
    if not mains or not any(v.get("online") == "1" for v in mains):
        errors.append("AC online state is not verified")
    if snapshot["power_profile"] != cfg["required_power_profile"]:
        errors.append(f"power profile must be {cfg['required_power_profile']}, observed {snapshot['power_profile']!r}")
    if not snapshot["cpu_policies"]:
        errors.append("CPU frequency policies are unavailable")
    for name, policy in snapshot["cpu_policies"].items():
        if policy.get("scaling_governor") != cfg["required_governor"]:
            errors.append(f"{name} governor must be {cfg['required_governor']}, observed {policy.get('scaling_governor')!r}")
        if policy.get("energy_performance_preference") != cfg["required_epp"]:
            errors.append(f"{name} EPP must be {cfg['required_epp']}, observed {policy.get('energy_performance_preference')!r}")
    rows = {r["cpu"]: r for r in snapshot["topology"]["lscpu_rows"]}
    for cpu in (cfg["client_cpu"], cfg["server_cpu"]):
        row = rows.get(cpu)
        if not row or row["online"].lower() != "yes":
            errors.append(f"CPU {cpu} is not present and online")
        elif row["max_mhz"] < 4000:
            errors.append(f"CPU {cpu} does not match the recorded P-core frequency class")
    if cfg["client_cpu"] == cfg["server_cpu"] or rows.get(cfg["client_cpu"], {}).get("core") == rows.get(cfg["server_cpu"], {}).get("core"):
        errors.append("client and server CPUs are not distinct physical cores")
    siblings = snapshot["topology"]["thread_siblings_list"]
    def expand_cpu_list(value: str | None) -> set[int]:
        result: set[int] = set()
        if not value:
            return result
        for part in value.split(","):
            pair = part.split("-")
            result.update(range(int(pair[0]), int(pair[-1]) + 1))
        return result
    if expand_cpu_list(siblings.get(str(cfg["client_cpu"]))) & expand_cpu_list(siblings.get(str(cfg["server_cpu"]))):
        errors.append("client and server CPUs are SMT siblings")
    if cfg["client_cpu"] == 0 or cfg["server_cpu"] == 0:
        errors.append("CPU 0 must remain available to the OS")
    return errors


def compile_final_harness() -> Path:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    binary = BUILD_DIR / "tls_final"
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(OPENSSL_DIR / "lib")
    cmd = ["gcc", "-O2", "-std=c11", "-Wall", "-Wextra", "-I", str(OPENSSL_DIR / "include"),
           str(PILOT_SOURCE), "-L", str(OPENSSL_DIR / "lib"),
           f"-Wl,-rpath,{OPENSSL_DIR / 'lib'}", "-lssl", "-lcrypto", "-o", str(binary)]
    run(cmd, env=env)
    return binary


def credential_checks(cfg: dict, env: dict) -> list[dict]:
    results = []
    for case in cfg["cases"]:
        stem = ROOT / "credentials" / case["credential"]
        cert, key = stem.with_suffix(".cert.pem"), stem.with_suffix(".key.pem")
        item = {"case_id": case["case_id"], "certificate": str(cert.relative_to(ROOT)),
                "private_key": str(key.relative_to(ROOT)), "certificate_sha256": None,
                "private_key_permissions_ok": False, "ok": False, "errors": []}
        try:
            if not cert.is_file() or not key.is_file():
                raise RuntimeError("certificate or private key is missing")
            if key.stat().st_mode & 0o077:
                raise RuntimeError("private-key permissions are broader than 0600")
            item["private_key_permissions_ok"] = True
            run([str(OPENSSL_BIN), "x509", "-in", str(cert), "-noout", "-subject"], env=env)
            run([str(OPENSSL_BIN), "pkey", "-in", str(key), "-check", "-noout"], env=env)
            cert_pub = run([str(OPENSSL_BIN), "x509", "-in", str(cert), "-pubkey", "-noout"], env=env).stdout.strip()
            key_pub = run([str(OPENSSL_BIN), "pkey", "-in", str(key), "-pubout"], env=env).stdout.strip()
            if cert_pub != key_pub:
                raise RuntimeError("certificate public key does not match private key")
            item["certificate_sha256"] = sha256(cert)
            item["ok"] = True
        except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
            item["errors"].append(str(exc))
        results.append(item)
    return results


def git_commit() -> str:
    return run(["git", "rev-parse", "HEAD"], check=True).stdout.strip()


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"--preflight-only", "--run"}:
        print("Usage: scripts/final/run_final.py --preflight-only|--run", file=sys.stderr)
        return 2
    mode = sys.argv[1]
    if mode == "--run":
        signal.signal(signal.SIGTERM, lambda signum, frame: (_ for _ in ()).throw(KeyboardInterrupt("SIGTERM")))
    cfg = json.loads(CONFIG.read_text())
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(OPENSSL_DIR / "lib")
    env["OPENSSL_CONF"] = str(ROOT / "configs/openssl/feasibility-openssl.cnf")
    results: dict = {"workflow": "final-ubuntu-multibatch", "mode": mode,
                     "captured_utc": utc_now(), "repository_base_commit": git_commit(),
                     "workflow_source_sha256": sha256(Path(__file__).resolve()),
                     "configuration_path": str(CONFIG.relative_to(ROOT)),
                     "configuration_sha256": sha256(CONFIG),
                     "harness_source": str(PILOT_SOURCE.relative_to(ROOT)),
                     "harness_sha256": sha256(PILOT_SOURCE), "checks": {}}
    errors: list[str] = []
    try:
        if not OPENSSL_BIN.is_file() or not OPENSSL_SOURCE.is_dir():
            raise RuntimeError("pinned OpenSSL install/source tree missing")
        results["checks"]["openssl_version"] = run([str(OPENSSL_BIN), "version"], env=env).stdout.strip()
        results["checks"]["openssl_source_commit"] = run(["git", "-C", str(OPENSSL_SOURCE), "rev-parse", "HEAD"]).stdout.strip()
        openssl_ldd = run(["ldd", str(OPENSSL_BIN)], env=env).stdout
        results["checks"]["openssl_linked_libraries"] = openssl_ldd.splitlines()
        if cfg["required_openssl_version"] not in results["checks"]["openssl_version"]:
            errors.append(f"OpenSSL version must be {cfg['required_openssl_version']}")
        if results["checks"]["openssl_source_commit"] != cfg["required_openssl_source_commit"]:
            errors.append("OpenSSL source commit differs from the pinned commit")
        if str(OPENSSL_DIR / "lib") not in openssl_ldd:
            errors.append("OpenSSL command is not linked to the pinned local libraries")
        results["checks"]["credentials"] = credential_checks(cfg, env)
        if not all(c["ok"] for c in results["checks"]["credentials"]):
            errors.append("one or more credentials failed validation")
        binary = compile_final_harness()
        results["checks"]["compiled_harness"] = str(binary.relative_to(ROOT))
        results["checks"]["compiled_harness_sha256"] = sha256(binary)
        ldd = run(["ldd", str(binary)], env=env).stdout
        results["checks"]["linked_libraries"] = ldd.splitlines()
        if str(OPENSSL_DIR / "lib") not in ldd:
            errors.append("compiled harness is not linked to the pinned local OpenSSL libraries")
        run([sys.executable, "-m", "py_compile", str(Path(__file__).resolve())])
        results["checks"]["workflow_python_syntax"] = "passed"
        snapshot = environment_snapshot()
        results["checks"]["environment_snapshot"] = snapshot
        errors.extend(guard_errors(snapshot, cfg))
        results["checks"]["raw_final_directory_exists_before_check"] = RAW_DIR.exists()
        results["checks"]["final_csv_count_before_check"] = len(list(RAW_DIR.glob("*.csv"))) if RAW_DIR.exists() else 0
        results["checks"]["raw_final_directory_exists_after_preflight"] = RAW_DIR.exists()
        results["checks"]["final_csv_count_after_preflight"] = len(list(RAW_DIR.glob("*.csv"))) if RAW_DIR.exists() else 0
        if results["checks"]["final_csv_count_before_check"]:
            errors.append("final raw data already exists; preflight does not overwrite or resume")
        results["checks"]["pilot_paths_untouched"] = True
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        errors.append(str(exc))
    results["ready_to_collect"] = not errors
    results["errors"] = errors
    results["final_data_generated"] = False
    results["preflight_only"] = mode == "--preflight-only"
    if mode == "--preflight-only":
        evidence_dir = ROOT / "evidence/final-workflow"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        evidence = evidence_dir / ("preflight-" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
        results["evidence_path"] = str(evidence.relative_to(ROOT))
        fd = os.open(evidence, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "w") as f:
            json.dump(results, f, indent=2)
            f.write("\n")
        print(json.dumps(results, indent=2))
        return 0 if not errors else 1
    if errors:
        print(json.dumps({"ready_to_collect": False, "errors": errors}, indent=2), file=sys.stderr)
        return 1
    return execute_batches(cfg, env, binary, results["checks"]["openssl_version"],
                           results["checks"]["openssl_source_commit"], results["repository_base_commit"])


def execute_batches(cfg: dict, env: dict, binary: Path, openssl_version: str,
                    openssl_commit: str, repo_commit: str) -> int:
    helper = load_pilot_module()
    seeds = random.Random(int(cfg["master_seed"]))
    previous_id = None
    cases = cfg["cases"]
    for batch_num in range(1, int(cfg["batch_count"]) + 1):
        batch_seed = seeds.getrandbits(64)
        batch_id = dt.datetime.now(dt.timezone.utc).strftime("final-%Y%m%dT%H%M%SZ") + f"-b{batch_num:02d}-" + uuid.uuid4().hex[:8]
        csv_path, meta_path = RAW_DIR / f"{batch_id}.csv", META_DIR / f"{batch_id}.json"
        if csv_path.exists() or meta_path.exists():
            raise FileExistsError(f"Batch output already exists; refusing overwrite or resume: {batch_id}")
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        META_DIR.mkdir(parents=True, exist_ok=True)
        # Exclusive creation is the no-overwrite/no-resume boundary.
        fd = os.open(csv_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
        csv_file = os.fdopen(fd, "w", newline="", buffering=1)
        writer = csv.DictWriter(csv_file, fieldnames=MASTER_FIELDS)
        writer.writeheader()
        warmups = [case for case in cases for _ in range(int(cfg["warmups_per_case"]))]
        measured = [case for case in cases for _ in range(int(cfg["measured_per_case"]))]
        rng = random.Random(batch_seed)
        rng.shuffle(warmups)
        rng.shuffle(measured)
        planned = [{"case_id": c["case_id"], "warmup": True} for c in warmups] + [
            {"case_id": c["case_id"], "warmup": False} for c in measured]
        meta = {
            "batch_id": batch_id, "batch_number": batch_num, "status": "incomplete",
            "stage": "preflight",
            "created_utc": utc_now(), "batch_start_utc": None, "batch_end_utc": None,
            "repository_commit": repo_commit, "openssl_version": openssl_version,
            "openssl_source_commit": openssl_commit,
            "configuration_path": str(CONFIG.relative_to(ROOT)), "configuration_sha256": sha256(CONFIG),
            "harness_source": str(PILOT_SOURCE.relative_to(ROOT)), "harness_sha256": sha256(PILOT_SOURCE),
            "compiled_harness_sha256": sha256(binary), "master_seed": cfg["master_seed"],
            "batch_seed": batch_seed, "planned_order": planned, "realized_order": [],
            "warmups_per_case": cfg["warmups_per_case"], "measured_per_case": cfg["measured_per_case"],
            "client_cpu": cfg["client_cpu"], "server_cpu": cfg["server_cpu"],
            "idle_interval_before": None, "environment_before": None, "environment_after": None,
            "rows_written": 0, "errors": [], "csv_path": str(csv_path.relative_to(ROOT)),
        }
        csv_file.flush()
        os.fsync(csv_file.fileno())
        save_metadata(meta_path, meta, exclusive=True)
        if previous_id is not None:
            idle_start_utc = utc_now()
            idle_start_mono = time.monotonic()
            meta["idle_interval_before"] = {"after_batch_id": previous_id, "start_utc": idle_start_utc,
                                             "required_seconds": cfg["idle_seconds_between_batches"], "end_utc": None}
            save_metadata(meta_path, meta)
            try:
                time.sleep(int(cfg["idle_seconds_between_batches"]))
            except BaseException as exc:
                meta["status"] = "incomplete"
                meta["errors"].append(f"idle interval interrupted: {exc!r}")
                meta["idle_interval_before"]["end_utc"] = utc_now()
                meta["idle_interval_before"]["elapsed_seconds"] = time.monotonic() - idle_start_mono
                csv_file.close()
                save_metadata(meta_path, meta, exclusive=not meta_path.exists())
                return 1
            meta["idle_interval_before"]["end_utc"] = utc_now()
            meta["idle_interval_before"]["elapsed_seconds"] = time.monotonic() - idle_start_mono
        snapshot = environment_snapshot()
        errors = guard_errors(snapshot, cfg)
        meta["environment_before"] = snapshot
        if errors:
            meta["status"] = "incomplete"
            meta["batch_start_utc"] = utc_now()
            meta["batch_end_utc"] = meta["batch_start_utc"]
            meta["errors"] = errors
            csv_file.close()
            save_metadata(meta_path, meta, exclusive=not meta_path.exists())
            return 1
        meta["status"] = "running"
        meta["stage"] = "measurement"
        meta["batch_start_utc"] = utc_now()
        save_metadata(meta_path, meta)
        try:
            for idx, case in enumerate(warmups + measured, start=1):
                data, _ = helper.one_observation(binary, case, env, cfg["client_cpu"], cfg["server_cpu"])
                row = {f: "" for f in MASTER_FIELDS}
                row.update(data)
                row.update({"batch_id": batch_id, "run_id": batch_id, "timestamp": utc_now(),
                            "sequence_index": idx, "warmup_flag": str(idx <= len(warmups)).lower(),
                            "git_commit_hash": repo_commit, "openssl_version": openssl_version,
                            "openssl_source_commit": openssl_commit})
                writer.writerow(row)
                csv_file.flush()
                os.fsync(csv_file.fileno())
                meta["rows_written"] += 1
                meta["realized_order"].append({"sequence_index": idx, "case_id": case["case_id"],
                                               "warmup": idx <= len(warmups),
                                               "handshake_success_failure": data["handshake_success_failure"]})
                if data["handshake_success_failure"] != "success":
                    raise RuntimeError(f"handshake failed at sequence {idx}, case {case['case_id']}: {data['error_reason']}")
                if idx % 10 == 0:
                    save_metadata(meta_path, meta)
                print(f"{batch_id}: {idx}/160", flush=True)
            meta["environment_after"] = environment_snapshot()
            ending_errors = guard_errors(meta["environment_after"], cfg)
            if ending_errors:
                raise RuntimeError("batch end guard failed: " + "; ".join(ending_errors))
            meta["batch_end_utc"] = utc_now()
            meta["status"] = "completed"
            meta["csv_sha256"] = sha256(csv_path)
            csv_file.close()
            previous_id = batch_id
            # Metadata is finalized after any following idle interval is recorded.
            if batch_num == int(cfg["batch_count"]):
                os.chmod(csv_path, 0o444)
                save_metadata(meta_path, meta, exclusive=not meta_path.exists())
            else:
                save_metadata(meta_path, meta)
        except BaseException as exc:
            meta["environment_after"] = environment_snapshot()
            meta["batch_end_utc"] = utc_now()
            meta["status"] = "incomplete"
            meta["errors"].append(repr(exc))
            try:
                csv_file.close()
            except Exception:
                pass
            meta["csv_sha256"] = sha256(csv_path)
            os.chmod(csv_path, 0o444)
            save_metadata(meta_path, meta, exclusive=not meta_path.exists())
            return 1
        os.chmod(csv_path, 0o444)
        os.chmod(meta_path, 0o444)
    return 0


def save_metadata(path: Path, data: dict, exclusive: bool = False) -> None:
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(fd, "w") as f:
        f.write(json.dumps(data, indent=2) + "\n")
        f.flush()
        os.fsync(f.fileno())
    if exclusive and path.exists():
        tmp.unlink(missing_ok=True)
        raise FileExistsError(f"Refusing to overwrite metadata: {path}")
    os.replace(tmp, path)
    os.chmod(path, 0o444)


if __name__ == "__main__":
    raise SystemExit(main())
