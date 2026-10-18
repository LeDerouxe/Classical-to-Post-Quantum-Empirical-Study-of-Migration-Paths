#!/usr/bin/env python3
"""Run three fresh, loopback-only TLS 1.3 feasibility handshakes per case."""
from __future__ import annotations

import hashlib
import os
import re
import subprocess
import socket
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OPENSSL = ROOT / "third_party/openssl-3.5.9/install/bin/openssl"
OPENSSL_CONF = ROOT / "configs/openssl/feasibility-openssl.cnf"
CREDS = ROOT / "credentials"
LOGS = ROOT / "logs/feasibility"
SUMMARY = ROOT / "docs/FEASIBILITY_RESULTS.md"
CERT_REPORT = ROOT / "docs/FEASIBILITY_CREDENTIALS.md"
CIPHER = "TLS_AES_128_GCM_SHA256"
CASES = [
    ("S0", "x25519", "ECDSA", "ecdsa_secp256r1_sha256", "ecdsa"),
    ("S2", "X25519MLKEM768", "ECDSA", "ecdsa_secp256r1_sha256", "ecdsa"),
    ("S3", "X25519MLKEM768", "ML-DSA-65", "mldsa65", "mldsa"),
    ("S4", "MLKEM768", "ML-DSA-65", "mldsa65", "mldsa"),
]


def run(args: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(OPENSSL.parent.parent / "lib")
    env["OPENSSL_CONF"] = str(OPENSSL_CONF)
    return subprocess.run(args, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, timeout=timeout, check=False)


def record_cert(name: str, algorithm: str) -> tuple[Path, Path, str, dict[str, str]] | None:
    key, cert = CREDS / f"{name}.key.pem", CREDS / f"{name}.cert.pem"
    if not (key.exists() and cert.exists()):
        if algorithm == "ecdsa":
            gen = run([str(OPENSSL), "genpkey", "-algorithm", "EC", "-pkeyopt",
                       "ec_paramgen_curve:P-256", "-out", str(key)])
        else:
            gen = run([str(OPENSSL), "genpkey", "-algorithm", "ML-DSA-65", "-out", str(key)])
        (LOGS / f"{name}-keygen.log").write_text(gen.stdout)
        if gen.returncode:
            return None
        req_args = [str(OPENSSL), "req", "-new", "-x509", "-key", str(key),
                    "-config", str(OPENSSL_CONF), "-out", str(cert), "-days", "7",
                    "-subj", f"/CN={name}.localhost"]
        if algorithm == "ecdsa":
            req_args.append("-sha256")
        req = run(req_args)
        (LOGS / f"{name}-certgen.log").write_text(req.stdout)
        if req.returncode:
            return None
    key.chmod(0o600)
    inspect = run([str(OPENSSL), "x509", "-in", str(cert), "-noout", "-subject",
                   "-issuer", "-dates", "-fingerprint", "-sha256", "-text"])
    (LOGS / f"{name}-certificate-inspection.txt").write_text(inspect.stdout)
    if inspect.returncode:
        return None
    digest = hashlib.sha256(cert.read_bytes()).hexdigest()
    pubkey = re.search(r"Public Key Algorithm:\s*(.+)", inspect.stdout)
    signature = re.search(r"^\s+Signature Algorithm:\s*(.+)$", inspect.stdout, re.M)
    before = re.search(r"Not Before:\s*(.+)", inspect.stdout)
    after = re.search(r"Not After\s*:\s*(.+)", inspect.stdout)
    fingerprint = re.search(r"sha256 Fingerprint=(.+)", inspect.stdout)
    details = {
        "public_key": pubkey.group(1).strip() if pubkey else "not reported",
        "signature": signature.group(1).strip() if signature else "not reported",
        "not_before": before.group(1).strip() if before else "not reported",
        "not_after": after.group(1).strip() if after else "not reported",
        "fingerprint": fingerprint.group(1).strip() if fingerprint else "not reported",
        "file_sha256": digest,
    }
    return key, cert, digest, details


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def one_handshake(case: str, group: str, sigalg: str, key: Path, cert: Path,
                  trial: int) -> tuple[bool, str, str, str]:
    port = free_port()
    stem = f"{case}-run{trial}"
    server_log, client_log = LOGS / f"{stem}-server.log", LOGS / f"{stem}-client.log"
    server_args = [str(OPENSSL), "s_server", "-accept", f"127.0.0.1:{port}",
                   "-tls1_3", "-no_ticket", "-groups", group, "-sigalgs", sigalg,
                   "-ciphersuites", CIPHER, "-cert", str(cert), "-key", str(key),
                   "-naccept", "1", "-www"]
    with server_log.open("w") as sf:
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = str(OPENSSL.parent.parent / "lib")
        env["OPENSSL_CONF"] = str(OPENSSL_CONF)
        server = subprocess.Popen(server_args, env=env, stdout=sf, stderr=subprocess.STDOUT, text=True)
        try:
            # Do not probe the listener with a TCP connection: -naccept 1 would
            # count that as the trial and consume the fresh server process.
            time.sleep(0.25)
            if server.poll() is not None:
                client_out = "server did not become ready"
            else:
                client_args = [str(OPENSSL), "s_client", "-connect", f"127.0.0.1:{port}",
                               "-tls1_3", "-no_ticket", "-brief",
                               "-groups", group, "-sigalgs", sigalg,
                               "-ciphersuites", CIPHER, "-CAfile", str(cert),
                               "-verify_return_error"]
                try:
                    cp = subprocess.run(client_args, input="", text=True, env=env,
                                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        timeout=20, check=False)
                    client_out = cp.stdout
                except subprocess.TimeoutExpired as exc:
                    client_out = (exc.stdout or "") + "\nclient timed out"
            client_log.write_text(client_out)
        finally:
            if server.poll() is None:
                server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    text = client_log.read_text(errors="replace")
    tls = "TLSv1.3" if "Protocol version: TLSv1.3" in text else ""
    group_match = re.search(r"(?:Negotiated TLS1\.3 group|Peer Temp Key|Server Temp Key):\s*(.+)", text)
    observed_group = group_match.group(1).strip() if group_match else ""
    sig_match = re.search(r"Signature type:\s*(.+)", text)
    observed_sig = sig_match.group(1).strip() if sig_match else ""
    ok = tls == "TLSv1.3" and "Verification: OK" in text and observed_sig.lower() == sigalg.lower()
    ok = ok and (group.lower() in observed_group.lower() or group.lower() == observed_group.lower())
    return ok, tls or "not negotiated", observed_group or "not reported", text


def main() -> None:
    if not OPENSSL.is_file():
        raise SystemExit(f"Research OpenSSL binary missing: {OPENSSL}")
    CREDS.mkdir(mode=0o700, parents=True, exist_ok=True)
    LOGS.mkdir(mode=0o700, parents=True, exist_ok=True)
    CREDS.chmod(0o700)
    LOGS.chmod(0o700)
    os.umask(0o077)
    groups_output = run([str(OPENSSL), "list", "-tls-groups"]).stdout
    results = []
    cert_details: dict[str, dict[str, str]] = {}
    for case, group, cert_type, sigalg, credname in CASES:
        cert_data = record_cert(credname, credname)
        matching_group = any(line.strip().split(":")[-1].strip().lower() == group.lower()
                             or re.search(rf"\b{re.escape(group)}\b", line, re.I)
                             for line in groups_output.splitlines())
        if cert_data is None:
            reason = f"Could not generate/inspect {cert_type} certificate; see logs/feasibility/{credname}-*.log"
            results.append((case, group, "not negotiated", cert_type, "unavailable", "not negotiated", 0,
                            "unavailable", f"logs/feasibility/{case}-run*.log", reason))
            continue
        key, cert, cert_hash, details = cert_data
        cert_details[credname] = details
        if not matching_group:
            (LOGS / f"{case}-availability.txt").write_text(
                f"Requested group {group} is absent from `openssl list -tls-groups`.\n"
                f"OpenSSL source inventory: environment/ubuntu-26.04.1/openssl-inventory.txt\n"
                f"Certificate SHA-256: {cert_hash}\nNo handshake was attempted because the group is unavailable.\n")
            results.append((case, group, "not negotiated", cert_type, "ML-DSA-65" if credname == "mldsa" else "ECDSA",
                            "not negotiated", 0, "unavailable", f"logs/feasibility/{case}-availability.txt",
                            f"Requested group {group} is not listed by this OpenSSL build; no handshake attempted. Certificate SHA-256: {cert_hash}."))
            continue
        passed, observed, version, reasons = 0, "not reported", "not negotiated", []
        for trial in range(1, 4):
            good, tls, found_group, output = one_handshake(case, group, sigalg, key, cert, trial)
            version = tls
            observed = found_group
            if good:
                passed += 1
            else:
                reasons.append(f"run {trial}: {output.strip()[-500:]}")
        if passed == 3:
            status, reason = "passed", f"All three fresh TLS 1.3 handshakes verified TLS_AES_128_GCM_SHA256, the requested group, certificate, and signature type. Certificate SHA-256: {cert_hash}."
        elif passed:
            status = "failed"
            reason = "; ".join(reasons) or "One or more runs did not match the requested behavior."
        else:
            status = "failed"
            reason = "; ".join(reasons) or "No run completed with the requested behavior."
        observed_key = "ECDSA" if credname == "ecdsa" else "ML-DSA-65"
        results.append((case, group, observed, cert_type, observed_key, version, passed,
                        status, f"logs/feasibility/{case}-run*.log", reason))

    headers = ["Case ID", "Requested group", "Observed group", "Requested certificate/key type",
               "Observed certificate/key type", "TLS version", "Runs passed / 3", "Status",
               "Evidence log path", "Notes"]
    lines = ["# TLS 1.3 Feasibility Results", "", "Feasibility evidence only; no performance or pilot measurements were run.",
             "All cases used TLS_AES_128_GCM_SHA256. Requested group spellings follow `openssl list -tls-groups`; this build exposes the standalone ML-KEM-768 group as `MLKEM768`.", "",
             "| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in results:
        cells = [str(x).replace("|", "\\|").replace("\n", " ") for x in row]
        lines.append("| " + " | ".join(cells) + " |")
    SUMMARY.write_text("\n".join(lines) + "\n")
    credential_lines = ["# Feasibility Test Credentials", "",
                        "Locally generated, self-signed, seven-day test certificates. Private keys and PEM certificates remain in ignored `credentials/`.", "",
                        "| Credential | Public-key algorithm | Certificate signature algorithm | Valid from (UTC) | Valid until (UTC) | Certificate SHA-256 | OpenSSL fingerprint SHA-256 |",
                        "|---|---|---|---|---|---|---|"]
    for name, d in cert_details.items():
        credential_lines.append("| " + " | ".join([name, d["public_key"], d["signature"], d["not_before"],
                                                         d["not_after"], d["file_sha256"], d["fingerprint"]]) + " |")
    CERT_REPORT.write_text("\n".join(credential_lines) + "\n")
    print(SUMMARY)
    for row in results:
        print(f"{row[0]}: {row[7]} ({row[6]}/3), group={row[2]}; {row[9]}")


if __name__ == "__main__":
    main()
