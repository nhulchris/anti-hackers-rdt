#!/usr/bin/env bash
# setup_netem.sh -- apply packet loss and delay to an interface for testing.
# Task 4 (Neha Virani).
#
# Usage:   sudo ./setup_netem.sh <interface> <loss%> <delay_ms>
# Example: sudo ./setup_netem.sh lo 5 20      # 5% loss, 20ms delay on loopback
# Clear:   sudo tc qdisc del dev <interface> root
#
# Note: works on Linux (the lab/Docker environment). On the loopback interface (lo)
# this lets you test sender and receiver on one machine under controlled conditions.

IFACE="${1:-lo}"
LOSS="${2:-0}"
DELAY="${3:-0}"

# Use tc directly in a root-owned Docker lab, or sudo on a normal Linux host.
if [[ "$EUID" -eq 0 ]]; then
    TC=(tc)
else
    TC=(sudo tc)
fi

# Replace any existing rule so interrupted experiment runs can restart cleanly.
"${TC[@]}" qdisc replace dev "$IFACE" root netem loss "${LOSS}%" delay "${DELAY}ms"

echo "Applied ${LOSS}% loss and ${DELAY}ms delay on ${IFACE}."
echo "Clear it with: sudo tc qdisc del dev ${IFACE} root"
