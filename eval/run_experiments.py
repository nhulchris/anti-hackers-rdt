"""Sweep loss/delay settings and measure the RDT implementation (Task 4: Neha)."""

import argparse
import csv
import multiprocessing as mp
import os
import platform
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

import constants  # noqa: E402
from packet import DATA  # noqa: E402
from receiver import Receiver  # noqa: E402
from sender import Sender  # noqa: E402


LOSS_RATES = [0, 1, 5, 10, 20]  # percent
DELAYS_MS = [0, 20, 100]
CSV_FIELDS = [
    "loss_pct",
    "delay_ms",
    "payload_bytes",
    "wire_bytes",
    "data_packets",
    "retransmissions",
    "completion_seconds",
    "throughput_mbps",
    "goodput_mbps",
    "verified",
    "simulated",
]


def _make_payload(size):
    """Build repeatable test data without needing a checked-in binary file."""
    pattern = b"The Anti-Hackers reliable UDP test data.\n"
    repeats = (size + len(pattern) - 1) // len(pattern)
    return (pattern * repeats)[:size]


def _transfer_worker(result_queue, payload, sim_loss_pct=0.0, sim_delay_ms=0.0):
    """Run one transfer in a child process so a stalled trial can be stopped."""
    receiver = None
    sender = None
    try:
        if sim_loss_pct or sim_delay_ms:
            _install_simulated_impairment(sim_loss_pct, sim_delay_ms)
        receiver = Receiver((constants.LOCALHOST, 0))
        port = receiver.sock.sock.getsockname()[1]
        received = {}

        def receive_data():
            received["data"] = receiver.receive()

        receiver_thread = threading.Thread(target=receive_data, daemon=True)
        receiver_thread.start()

        sender = Sender((constants.LOCALHOST, port))
        original_send = sender.sock.send
        counters = {"wire_bytes": 0, "data_packets": 0}
        seen_sequences = set()

        def counted_send(packet, address):
            counters["wire_bytes"] += len(packet.pack())
            if packet.has_flag(DATA):
                counters["data_packets"] += 1
                seen_sequences.add(packet.seq_num)
            original_send(packet, address)

        sender.sock.send = counted_send

        started = time.perf_counter()
        sender.send(payload)
        elapsed = time.perf_counter() - started
        sender.close()
        sender = None

        receiver_thread.join(timeout=3.0)
        if receiver_thread.is_alive():
            raise RuntimeError("receiver did not finish after the sender stopped")

        delivered = received.get("data", b"")
        retransmissions = counters["data_packets"] - len(seen_sequences)
        result_queue.put(
            {
                "payload_bytes": len(payload),
                "wire_bytes": counters["wire_bytes"],
                "data_packets": counters["data_packets"],
                "retransmissions": retransmissions,
                "completion_seconds": round(elapsed, 6),
                "throughput_mbps": round(counters["wire_bytes"] * 8 / elapsed / 1_000_000, 6),
                "goodput_mbps": round(len(delivered) * 8 / elapsed / 1_000_000, 6),
                "verified": delivered == payload,
            }
        )
    except Exception as exc:
        result_queue.put({"error": f"{type(exc).__name__}: {exc}"})
    finally:
        if sender is not None:
            sender.close()
        if receiver is not None:
            receiver.close()


def _install_simulated_impairment(loss_pct, delay_ms):
    """Software substitute for tc/netem: drop and delay outgoing datagrams.

    Patches UDPSocket.send in this process so BOTH directions (data and ACKs)
    experience loss/delay, approximating what netem does on the loopback device.
    Results produced this way are labeled simulated=yes in the CSV.
    """
    import random
    import socket_layer

    rng = random.Random(4600)  # fixed seed -> reproducible runs
    real_send = socket_layer.UDPSocket.send
    p_drop = loss_pct / 100.0
    delay_s = delay_ms / 1000.0 / 2.0  # netem delay is per direction; split RTT evenly

    def impaired_send(self, packet, addr):
        if p_drop and rng.random() < p_drop:
            return  # dropped on the wire
        if delay_s:
            timer = threading.Timer(delay_s, real_send, args=(self, packet, addr))
            timer.daemon = True
            timer.start()
        else:
            real_send(self, packet, addr)

    socket_layer.UDPSocket.send = impaired_send


def _run_transfer(payload_size, timeout, sim_loss_pct=0.0, sim_delay_ms=0.0):
    result_queue = mp.Queue()
    process = mp.Process(
        target=_transfer_worker,
        args=(result_queue, _make_payload(payload_size), sim_loss_pct, sim_delay_ms),
    )
    process.start()
    process.join(timeout=timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        raise TimeoutError(f"transfer did not finish within {timeout} seconds")

    try:
        result = result_queue.get(timeout=2.0)
    except queue.Empty as exc:
        raise RuntimeError(f"transfer process exited with code {process.exitcode}") from exc

    if "error" in result:
        raise RuntimeError(result["error"])
    if not result["verified"]:
        raise RuntimeError("received data did not match the test payload")
    return result


def apply_netem(interface, loss_pct, delay_ms):
    """Apply a Linux tc/netem rule using the project setup script."""
    if platform.system() != "Linux":
        raise RuntimeError("tc/netem experiments require Linux or the Docker lab")

    script = Path(__file__).with_name("setup_netem.sh")
    subprocess.run(
        ["bash", str(script), interface, str(loss_pct), str(delay_ms)],
        check=True,
    )


def clear_netem(interface):
    """Remove the test qdisc, ignoring the error when no rule is present."""
    if platform.system() != "Linux":
        return

    command = ["tc", "qdisc", "del", "dev", interface, "root"]
    if os.geteuid() != 0:
        command.insert(0, "sudo")
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run_one(
    loss_pct,
    delay_ms,
    interface="lo",
    payload_size=256 * 1024,
    timeout=60,
    mode="netem",
):
    """Run one transfer and return its configuration and measured metrics.

    mode: "netem"    -> real kernel impairment via tc/netem (Linux only)
          "simulate" -> software loss/delay injected at the socket layer (any OS)
          "baseline" -> no impairment; loss/delay must be 0
    """
    sim_loss = sim_delay = 0.0
    if mode == "netem":
        apply_netem(interface, loss_pct, delay_ms)
    elif mode == "simulate":
        sim_loss, sim_delay = loss_pct, delay_ms
    elif loss_pct != 0 or delay_ms != 0:
        raise ValueError("nonzero loss/delay values require netem or --simulate-loss")

    result = _run_transfer(payload_size, timeout, sim_loss, sim_delay)
    result["loss_pct"] = loss_pct
    result["delay_ms"] = delay_ms
    result["simulated"] = "yes" if mode == "simulate" else "no"
    return result


def write_csv(results, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(results)


def make_plot(results, output_path):
    """Plot throughput and goodput against packet-loss percentage."""
    output_path = Path(output_path)
    mpl_config = output_path.parent / ".mplconfig"
    mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_config))

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))

    for delay_ms in sorted({row["delay_ms"] for row in results}):
        rows = sorted(
            (row for row in results if row["delay_ms"] == delay_ms),
            key=lambda row: row["loss_pct"],
        )
        losses = [row["loss_pct"] for row in rows]
        axes[0].plot(losses, [row["throughput_mbps"] for row in rows], marker="o",
                     label=f"{delay_ms} ms")
        axes[1].plot(losses, [row["goodput_mbps"] for row in rows], marker="o",
                     label=f"{delay_ms} ms")

    axes[0].set_title("Throughput")
    axes[1].set_title("Goodput")
    for axis in axes:
        axis.set_xlabel("Packet loss (%)")
        axis.set_ylabel("Mbps")
        axis.grid(True, alpha=0.3)
        axis.legend(title="Delay")

    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def _number_list(value):
    try:
        return [float(item.strip()) for item in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use comma-separated numbers") from exc


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--loss-rates", type=_number_list, default=LOSS_RATES)
    parser.add_argument("--delays", type=_number_list, default=DELAYS_MS)
    parser.add_argument("--interface", default="lo")
    parser.add_argument("--payload-bytes", type=int, default=256 * 1024)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--output-csv", default=str(PROJECT_ROOT / "eval" / "results.csv"))
    parser.add_argument("--plot", default=str(PROJECT_ROOT / "eval" / "plots" / "performance.png"))
    parser.add_argument(
        "--skip-netem",
        action="store_true",
        help="run only a 0%% loss/0 ms local baseline without changing network rules",
    )
    parser.add_argument(
        "--simulate-loss",
        action="store_true",
        help="inject loss/delay in software at the socket layer (no netem/Linux needed); "
             "results are labeled simulated in the CSV",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.payload_bytes <= 0:
        raise SystemExit("--payload-bytes must be positive")
    if args.skip_netem and args.simulate_loss:
        raise SystemExit("choose one of --skip-netem or --simulate-loss")
    if args.skip_netem and (args.loss_rates != [0] or args.delays != [0]):
        raise SystemExit("--skip-netem requires --loss-rates 0 --delays 0")

    if args.simulate_loss:
        mode = "simulate"
    elif args.skip_netem:
        mode = "baseline"
    else:
        mode = "netem"

    results = []
    try:
        for delay_ms in args.delays:
            for loss_pct in args.loss_rates:
                print(f"Running loss={loss_pct}% delay={delay_ms}ms ...", flush=True)
                row = run_one(
                    loss_pct,
                    delay_ms,
                    interface=args.interface,
                    payload_size=args.payload_bytes,
                    timeout=args.timeout,
                    mode=mode,
                )
                results.append(row)
                write_csv(results, args.output_csv)
                print(
                    f"  {row['completion_seconds']:.3f}s, "
                    f"goodput={row['goodput_mbps']:.3f} Mbps, "
                    f"retransmissions={row['retransmissions']}"
                )
    finally:
        if mode == "netem":
            clear_netem(args.interface)

    make_plot(results, args.plot)
    print(f"Saved raw results to {args.output_csv}")
    print(f"Saved plot to {args.plot}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
