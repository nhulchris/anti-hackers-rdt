"""
run_experiments.py -- Sweep loss rates / RTTs and collect metrics (Task 4: Neha Virani).

TODO (Neha):
  - For each loss rate in LOSS_RATES: apply netem (setup_netem.sh), run a transfer
    between the sender and receiver, and record throughput, goodput, retransmission
    count, and completion time.
  - Save results to a CSV, then plot them with matplotlib (e.g. throughput vs loss rate).

This is what produces the graphs for the final report, so keep the raw numbers.
"""

# import csv, subprocess, time
# import matplotlib.pyplot as plt

LOSS_RATES = [0, 1, 5, 10, 20]    # percent
DELAYS_MS = [0, 20, 100]          # round-trip delay variants


def run_one(loss_pct, delay_ms):
    """
    TODO (Neha): apply netem for (loss_pct, delay_ms), run sender + receiver on a
    test file, time the transfer, and return a dict of metrics.
    """
    raise NotImplementedError


def main():
    """TODO (Neha): loop over LOSS_RATES (and DELAYS_MS), call run_one, write CSV, plot."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
