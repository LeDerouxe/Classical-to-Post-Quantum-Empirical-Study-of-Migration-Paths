#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VERSION=3.5.9
COMMIT=45e844fa2a14ec92d146bd8f5778ac130b6625fb
WORK="$ROOT/third_party/openssl-$VERSION"
SOURCE="$WORK/source"
PREFIX="$WORK/install"

if [[ -e "$SOURCE" ]]; then
  actual="$(git -C "$SOURCE" rev-parse HEAD)"
  [[ "$actual" == "$COMMIT" ]] || { echo "Existing source is at $actual, expected $COMMIT" >&2; exit 1; }
else
  mkdir -p "$WORK"
  git clone --depth 1 --branch "openssl-$VERSION" https://github.com/openssl/openssl.git "$SOURCE"
fi

actual="$(git -C "$SOURCE" rev-parse HEAD)"
[[ "$actual" == "$COMMIT" ]] || { echo "Source commit mismatch: $actual" >&2; exit 1; }

cd "$SOURCE"
./Configure linux-x86_64 --prefix="$PREFIX" --openssldir="$PREFIX/ssl" --libdir=lib shared zlib
make -j"$(nproc)"
make install_sw
printf 'version=%s\ncommit=%s\nprefix=%s\n' "$VERSION" "$actual" "$PREFIX"
export LD_LIBRARY_PATH="$PREFIX/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
"$PREFIX/bin/openssl" version -a
