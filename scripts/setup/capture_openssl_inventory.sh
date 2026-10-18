#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OPENSSL_BIN="$ROOT/third_party/openssl-3.5.9/install/bin/openssl"
export LD_LIBRARY_PATH="$ROOT/third_party/openssl-3.5.9/install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export OPENSSL_CONF="$ROOT/configs/openssl/feasibility-openssl.cnf"
OUT="$ROOT/environment/ubuntu-26.04.1/openssl-inventory.txt"
[[ -x "$OPENSSL_BIN" ]] || { echo "Research OpenSSL not built: $OPENSSL_BIN" >&2; exit 1; }
{
  echo '$ openssl version -a'; "$OPENSSL_BIN" version -a
  echo; echo '$ openssl list -tls-groups'; "$OPENSSL_BIN" list -tls-groups
  echo; echo '$ openssl list -tls-signature-algorithms'; "$OPENSSL_BIN" list -tls-signature-algorithms
  echo; echo '$ openssl list -signature-algorithms'; "$OPENSSL_BIN" list -signature-algorithms
  echo; echo '$ openssl list -public-key-algorithms'; "$OPENSSL_BIN" list -public-key-algorithms
  echo; echo '$ openssl list -providers'; "$OPENSSL_BIN" list -providers
  echo; echo '$ exact candidate-name checks'
  for n in ML-KEM-768 MLKEM768 ML-DSA-65 X25519 X25519MLKEM768; do
    if "$OPENSSL_BIN" list -tls-groups 2>/dev/null | grep -Fq "$n"; then g=listed; else g=not-listed; fi
    if "$OPENSSL_BIN" list -signature-algorithms 2>/dev/null | grep -Fq "$n"; then s=listed; else s=not-listed; fi
    if "$OPENSSL_BIN" list -public-key-algorithms 2>/dev/null | grep -Fq "$n"; then p=listed; else p=not-listed; fi
    printf '%s: TLS-group=%s signature=%s public-key=%s\n' "$n" "$g" "$s" "$p"
  done
} | tee "$OUT"
