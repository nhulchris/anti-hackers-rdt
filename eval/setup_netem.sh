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

# Remove any existing rule first (ignore errors if none is set).
sudo tc qdisc del dev "$IFACE" root 2>/dev/null

sudo tc qdisc add dev "$IFACE" root netem loss "${LOSS}%" delay "${DELAY}ms"

echo "Applied ${LOSS}% loss and ${DELAY}ms delay on ${IFACE}."
echo "Clear it with: sudo tc qdisc del dev ${IFACE} root"
