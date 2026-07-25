"""
replot.py -- regenerate presentation-quality plots from an existing results.csv
without rerunning the sweep.  Usage:  python eval\replot.py

Reads eval/results.csv, writes eval/plots/performance_log.png (log-scale goodput +
retransmissions) alongside the original performance.png.
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EVAL_DIR = Path(__file__).resolve().parent
CSV_PATH = EVAL_DIR / "results.csv"
OUT_PATH = EVAL_DIR / "plots" / "performance_log.png"


def main():
    rows = list(csv.DictReader(CSV_PATH.open()))
    delays = sorted({int(r["delay_ms"]) for r in rows})

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    for delay in delays:
        pts = sorted(
            (r for r in rows if int(r["delay_ms"]) == delay),
            key=lambda r: float(r["loss_pct"]),
        )
        loss = [float(r["loss_pct"]) for r in pts]
        ax1.plot(loss, [float(r["goodput_mbps"]) for r in pts],
                 marker="o", label=f"{delay} ms")
        ax2.plot(loss, [int(r["retransmissions"]) for r in pts],
                 marker="s", label=f"{delay} ms")

    ax1.set_yscale("log")
    ax1.set_title("Goodput vs. packet loss (log scale)")
    ax1.set_xlabel("Packet loss (%)")
    ax1.set_ylabel("Goodput (Mbps, log)")
    ax1.grid(True, which="both", alpha=0.3)
    ax1.legend(title="Delay")

    ax2.set_title("Retransmissions vs. packet loss")
    ax2.set_xlabel("Packet loss (%)")
    ax2.set_ylabel("Retransmitted packets")
    ax2.grid(True, alpha=0.3)
    ax2.legend(title="Delay")

    fig.suptitle("Anti-Hackers RDT under simulated loss and delay (64 KB transfers)")
    fig.tight_layout()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PATH, dpi=150)
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
