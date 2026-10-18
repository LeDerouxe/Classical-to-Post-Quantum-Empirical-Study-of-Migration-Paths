# Ubuntu Environment Manifest

Collected: **2026-10-18 09:51:06 Asia/Tehran (UTC+03:30)**
Machine pseudonym: **primary-i5**
Platform statement: **Native Ubuntu 26.04.1 LTS on Intel Core i5-12450H.**

## Repository registration

The working directory is `/home/ae/Desktop/EXP`, an ext4 directory containing the handoff and protocol documents. It is not a Git repository. The researcher asked that phase files be created here for later organization. Therefore there is no active branch, repository URL, base commit, or repository commit hash to record, and no Git identity was configured. The official OpenSSL source checkout used for the research build is recorded below.

## Host and environment

| Item | Recorded value |
|---|---|
| OS | Ubuntu 26.04.1 LTS (Resolute Raccoon), `VERSION_ID=26.04` |
| Kernel | `7.0.0-38-generic` |
| CPU | 12th Gen Intel Core i5-12450H, x86_64 |
| CPU topology | 1 socket; 8 physical cores and 12 online logical CPUs. CPUs 0–7 are sibling pairs (four two-thread cores); CPUs 8–11 are four single-thread cores. One NUMA node. |
| Microcode | `0x43b` |
| RAM | 14 GiB; swap 4.0 GiB |
| Workspace filesystem | `/dev/nvme0n1p7`, ext4, mounted at `/` |
| CPU governor | `powersave` (CPU 0) |
| Energy-performance preference | `balance_performance` (CPU 0) |
| AC power | Connected (`ADP1 online=1`) |
| Background load | At collection: uptime 17 min; load averages 1.29, 1.99, 1.11; two logged-in users. Interactive desktop processes were active. |
| Hostname | Not recorded; pseudonym used. |

No governor, power, BIOS, swap, or kernel settings were changed.

## Tool versions

| Tool | Version |
|---|---|
| GCC | `gcc (Ubuntu 15.2.0-16ubuntu1) 15.2.0` |
| GNU Make | `GNU Make 4.4.1` |
| CMake | `cmake version 4.2.3` |
| Ninja | `1.13.2` |
| Python | `Python 3.14.4` |
| Git | `git version 2.53.0` |
| Perl | `5.40.1` |
| pkg-config | `2.5.1` |
| APT | `apt 3.2.0 (amd64)` |
| dpkg | `1.23.7 (amd64)` |

The researcher approved and ran installation of `build-essential`, `pkg-config`, `cmake`, `ninja-build`, `zlib1g-dev`, and `python3-venv`. The required tools are now present.

## Research OpenSSL build

| Item | Value |
|---|---|
| Upstream | [OpenSSL source repository](https://github.com/openssl/openssl) |
| Release line | OpenSSL 3.5 LTS |
| Selected stable patch | `openssl-3.5.9` (29 Sep 2026), latest 3.5 patch at collection time per the [official release timeline](https://mirror.openssl-library.org/news/timeline/) |
| Tag object | `d0ca66a1abe52545f14eca635c648932fcde5615` |
| Peeled source commit | `45e844fa2a14ec92d146bd8f5778ac130b6625fb` |
| Checkout verification | `git describe --tags --exact-match HEAD` returned `openssl-3.5.9`; `git rev-parse HEAD` matched the peeled commit above. `git ls-remote` returned the same tag object and peeled commit. |
| Tag signature | Tag is signed by RSA key `C46ED3F2CBEFDA1FDAADA44264ED7B1DCCE71CB2`; local verification could not complete because that public key is not in the local keyring. |
| Install prefix | `/home/ae/Desktop/EXP/third_party/openssl-3.5.9/install` |
| Build script | `scripts/setup/build_openssl.sh` |
| Build command | `./Configure linux-x86_64 --prefix=/home/ae/Desktop/EXP/third_party/openssl-3.5.9/install --openssldir=/home/ae/Desktop/EXP/third_party/openssl-3.5.9/install/ssl --libdir=lib shared zlib` |
| Build/install | `make -j12`; `make install_sw` |
| Compiler | GCC 15.2.0 |
| Build flags reported by OpenSSL | `-fPIC -pthread -m64 -Wa,--noexecstack -Wall -O3 -DOPENSSL_USE_NODELETE -DL_ENDIAN -DOPENSSL_PIC -DOPENSSL_BUILDING_OPENSSL -DZLIB -DNDEBUG` |
| Architecture-specific tuning | No custom CPU architecture flags were supplied. `-O3` is the OpenSSL target's default. |
| System OpenSSL | Not used for research handshakes; system version was 3.5.5. |
| FIPS/production | No FIPS or production claim. |

The source tag and commit were checked against the upstream Git repository before configuring. The signed tag's cryptographic signature remains unverified locally because its public key was unavailable.

### `openssl version -a`

```text
OpenSSL 3.5.9 29 Sep 2026 (Library: OpenSSL 3.5.9 29 Sep 2026)
built on: Sun Oct 18 06:17:41 2026 UTC
platform: linux-x86_64
options:  bn(64,64)
compiler: gcc -fPIC -pthread -m64 -Wa,--noexecstack -Wall -O3 -DOPENSSL_USE_NODELETE -DL_ENDIAN -DOPENSSL_PIC -DOPENSSL_BUILDING_OPENSSL -DZLIB -DNDEBUG
OPENSSLDIR: "/home/ae/Desktop/EXP/third_party/openssl-3.5.9/install/ssl"
ENGINESDIR: "/home/ae/Desktop/EXP/third_party/openssl-3.5.9/install/lib/engines-3"
MODULESDIR: "/home/ae/Desktop/EXP/third_party/openssl-3.5.9/install/lib/ossl-modules"
Seeding source: os-specific
CPUINFO: OPENSSL_ia32cap=0x7ffaf3ffffebffff:0x98c007bc239c27eb:0x00400810fc18c410:0x0000000000040000:0x0000000000000000
```

OpenSSL's build tree, install tree, generated keys/certificates, and run logs are excluded by `.gitignore`. The inventory is saved at `environment/ubuntu-26.04.1/openssl-inventory.txt`. Phase 1 invokes the research binary by absolute path and sets `LD_LIBRARY_PATH` to its local library directory. The controlled local configuration at `configs/openssl/feasibility-openssl.cnf` activates only the default provider.

## Phase 0 status

Environment registration, tool verification, pinned source build, and OpenSSL inventory are complete. Because this workspace is intentionally not a repository, no repository commit hash or commit was created. No benchmark data was generated.

## Repository Integration / Reproducibility Check

Check performed: **2026-10-18 11:15 Asia/Tehran (UTC+03:30)**.

| Item | Result |
|---|---|
| Repository URL | `https://github.com/LeDerouxe/Classical-to-Post-Quantum-Empirical-Study-of-Migration-Paths.git` |
| Branch | `main` (tracking `origin/main`) |
| Commit checked out before this documentation update | `736c5300e939501759ce232e88ba417e1f548c2b` |
| Native Linux clone path | `/home/ae/Desktop/EXP/ubuntu-study-repo` (ext4) |
| Research OpenSSL rebuilt from the repository script | OpenSSL `3.5.9`, source commit `45e844fa2a14ec92d146bd8f5778ac130b6625fb` |
| Rebuilt binary version | `OpenSSL 3.5.9 29 Sep 2026 (Library: OpenSSL 3.5.9 29 Sep 2026)` |
| Rebuilt binary install prefix | `/home/ae/Desktop/EXP/ubuntu-study-repo/third_party/openssl-3.5.9/install` |
| Inventory comparison | Algorithm, group, signature, public-key, provider, and candidate-name inventory is identical to the committed inventory after normalizing only build timestamp and clone-specific `OPENSSLDIR`, `ENGINESDIR`, and `MODULESDIR` paths. No functional inventory differences were found. |
| Build/output handling | `third_party/` is ignored by the repository `.gitignore`; it is not part of this documentation commit. |
| Phase boundary | No Phase 1 handshakes were rerun, no benchmark or pilot was run, and Phase 2 was not started. |

The captured inventory differs byte-for-byte from the committed copy only in the build timestamp and the three install-prefix paths above. The normalized comparison was identical. The existing committed inventory file was left unchanged so this update can remain documentation-only.
