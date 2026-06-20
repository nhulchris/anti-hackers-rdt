# Evaluation / Testbed (Task 4 -- Neha)

This folder holds the testbed and the experiment scripts that measure how the protocol
behaves under packet loss and delay.

## Files
- `setup_netem.sh` -- applies loss/delay to a network interface with `tc`/`netem`.
- `run_experiments.py` -- sweeps loss rates, runs transfers, records metrics, makes plots.

## Quick start (Linux)
```
# 1. Add 5% loss + 20ms delay on loopback:
sudo ./setup_netem.sh lo 5 20

# 2. (in src/) run the receiver, then the sender, and transfer a test file.

# 3. Clear the network conditions when done:
sudo tc qdisc del dev lo root
```

## Metrics to collect
- Throughput and goodput
- Number of retransmissions
- Transfer completion time
- (compare against a raw-UDP and a TCP baseline)
