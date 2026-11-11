#!/usr/bin/env bash
# Create, inspect, and remove only the dedicated network-sensitivity topology.
set -euo pipefail

client_ns=pqc-tls-client
server_ns=pqc-tls-server
client_if=veth-pqc-client
server_if=veth-pqc-server
client_ip=198.18.5.1/30
server_ip=198.18.5.2/30

[[ ${EUID} -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }

exists() { ip netns list | awk '{print $1}' | grep -Fxq "$1"; }

case ${1:-} in
  setup)
    if exists "$client_ns" || exists "$server_ns"; then
      echo "refusing setup: dedicated namespace already exists" >&2; exit 1
    fi
    ip netns add "$client_ns"
    ip netns add "$server_ns"
    ip link add "$client_if" netns "$client_ns" type veth peer name "$server_if" netns "$server_ns"
    ip -n "$client_ns" link set lo up
    ip -n "$server_ns" link set lo up
    ip -n "$client_ns" addr add "$client_ip" dev "$client_if"
    ip -n "$server_ns" addr add "$server_ip" dev "$server_if"
    ip -n "$client_ns" link set "$client_if" up
    ip -n "$server_ns" link set "$server_if" up
    ip -n "$client_ns" link set "$client_if" mtu 1500
    ip -n "$server_ns" link set "$server_if" mtu 1500
    echo "created isolated namespaces and veth link"
    ;;
  status)
    exists "$client_ns" && exists "$server_ns" || { echo "topology missing" >&2; exit 1; }
    ip -n "$client_ns" -brief addr show "$client_if"
    ip -n "$server_ns" -brief addr show "$server_if"
    ip -n "$client_ns" -s qdisc show dev "$client_if"
    ip -n "$server_ns" -s qdisc show dev "$server_if"
    ;;
  teardown)
    exists "$client_ns" && ip netns del "$client_ns" || true
    exists "$server_ns" && ip netns del "$server_ns" || true
    echo "removed only the dedicated network-sensitivity namespaces"
    ;;
  *) echo "usage: $0 setup|status|teardown" >&2; exit 2 ;;
esac
