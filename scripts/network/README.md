# Network-sensitivity workflow

This workflow is intentionally separate from the Ubuntu loopback and Windows
campaigns. It needs Ubuntu, the pinned local OpenSSL build, existing ignored
credentials, `iproute2`, and temporary `sudo` authorization.

First create the isolated topology, from the repository root:

```bash
sudo -v
sudo bash scripts/network/netns_topology.sh setup
sudo bash scripts/network/netns_topology.sh status
```

The runner has three modes:

```bash
python3 scripts/network/run_network.py --preflight-only
python3 scripts/network/run_network.py --smoke-test
python3 scripts/network/run_network.py --run
```

It never changes the host power policy. It uses `sudo -n` only to enter the
already-created dedicated namespaces and to replace their veth root qdiscs.
Preflight and smoke write evidence only. `--run` creates a single fresh,
non-resumable campaign with five delay conditions and five batches per
condition. Do not run it until the preflight and smoke evidence are reviewed.

After all evidence has been reviewed, remove the dedicated topology with:

```bash
sudo bash scripts/network/netns_topology.sh teardown
```
