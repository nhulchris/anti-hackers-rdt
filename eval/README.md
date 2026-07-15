# Evaluation / Testbed (Task 4 -- Neha)

This folder holds the testbed and the experiment scripts that measure how the protocol
behaves under packet loss and delay.

## Files
- `setup_netem.sh` -- applies loss/delay to a network interface with `tc`/`netem`.
- `run_experiments.py` -- sweeps loss rates, runs transfers, records metrics, makes plots.

## Full automated sweep (Linux/Docker lab)
```
python eval/run_experiments.py
```
The script tests every combination in `LOSS_RATES` and `DELAYS_MS`, applies `tc/netem`,
runs a real sender/receiver transfer, verifies the received bytes, and saves:

- `eval/results.csv` with the raw measurements
- `eval/plots/performance.png` with throughput and goodput graphs

If a smaller sweep is needed:
```
python eval/run_experiments.py --loss-rates 0,5,10 --delays 0,20
```

## Local baseline (no netem)
The following command works on Windows, macOS, or Linux and does not require root access:
```
python eval/run_experiments.py --skip-netem --loss-rates 0 --delays 0
```

## Manual netem setup
```
# Add 5% loss + 20ms delay on loopback:
./eval/setup_netem.sh lo 5 20

# In src/, run the receiver and sender to transfer a test file.

# Clear the network conditions when done:
sudo tc qdisc del dev lo root
```

## Metrics to collect
- Throughput and goodput
- Number of retransmissions
- Transfer completion time

`throughput_mbps` includes every sender packet placed on the wire, including
retransmissions. `goodput_mbps` counts only application bytes verified at the receiver.
