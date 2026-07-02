"""
sender.py -- Reliable sender (Task 2: Theophilus Cox).

Responsible for:
  - breaking application data into packets
  - the sliding window (Go-Back-N)
  - sequence numbering
  - retransmission timers / timeout handling
  - processing incoming ACKs

Coordinate the ACK format with Chris (Task 3) -- his ack_num is cumulative:
  ack_num = "next seq I expect", so we set base = ack_num on each ACK.
"""

import time

from socket_layer import UDPSocket
from packet import Packet, DATA, ACK, FIN
import constants

try:
    from congestion import CongestionControl
    _CONGESTION_AVAILABLE = True
except ImportError:
    _CONGESTION_AVAILABLE = False


class Sender:
    def __init__(self, dest_addr, bind_addr=None):
        self.sock = UDPSocket(bind_addr)
        self.dest_addr = dest_addr

        self.base = 0        # oldest unACKed sequence number
        self.next_seq = 0    # next sequence number to assign

        self.window = constants.DEFAULT_WINDOW
        self._timeout = constants.DEFAULT_TIMEOUT

        # seq_num -> Packet, kept for Go-Back-N retransmission
        self._unacked: dict = {}
        # wall-clock time when the base packet was (re)sent; None when nothing in flight
        self._timer_start: float | None = None

        # Task 4 integration: wire in congestion control, guard against NotImplementedError
        self._congestion = CongestionControl() if _CONGESTION_AVAILABLE else None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, data: bytes) -> None:
        """Reliably deliver `data` to the receiver using a Go-Back-N sliding window."""
        chunks = [
            data[i : i + constants.PAYLOAD_SIZE]
            for i in range(0, len(data), constants.PAYLOAD_SIZE)
        ]
        n = len(chunks)

        # Handle zero-length data gracefully
        if n == 0:
            self._send_fin()
            return

        while self.base < n:
            # --- fill the window with new packets ---
            while self.next_seq < n and (self.next_seq - self.base) < self._effective_window():
                pkt = Packet(
                    seq_num=self.next_seq,
                    flags=DATA,
                    payload=chunks[self.next_seq],
                )
                self._unacked[self.next_seq] = pkt
                self.sock.send(pkt, self.dest_addr)

                # Start the timer on the very first unACKed packet
                if self._timer_start is None:
                    self._timer_start = time.time()

                self.next_seq += 1

            # --- wait for an ACK, respecting the remaining timer budget ---
            remaining = self._remaining_timeout()
            if remaining <= 0:
                self._retransmit()
                continue

            ack_pkt, _ = self.sock.receive(timeout=remaining)

            if ack_pkt is None:
                # Timeout expired
                self._retransmit()
            elif ack_pkt.is_valid() and ack_pkt.has_flag(ACK):
                self._handle_ack(ack_pkt)
            # Corrupted or non-ACK packets are silently dropped; timer keeps running

        self._send_fin()

    def close(self) -> None:
        self.sock.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _handle_ack(self, pkt: Packet) -> None:
        """Advance the window base on a valid cumulative ACK."""
        new_base = pkt.ack_num

        if new_base <= self.base:
            # Duplicate or stale ACK -- nothing new confirmed
            return

        # Clear all packets that are now acknowledged
        for seq in range(self.base, new_base):
            self._unacked.pop(seq, None)

        self.base = new_base

        # Restart timer if there are still packets in flight; stop it if the window is clean
        if self._unacked:
            self._timer_start = time.time()
        else:
            self._timer_start = None

        self._notify_congestion_ack()

    def _retransmit(self) -> None:
        """Go-Back-N: resend every unACKed packet in sequence order."""
        self._notify_congestion_timeout()

        for seq in range(self.base, self.next_seq):
            pkt = self._unacked.get(seq)
            if pkt is not None:
                self.sock.send(pkt, self.dest_addr)

        self._timer_start = time.time()

    def _send_fin(self) -> None:
        """Send a FIN and wait for the receiver's FIN-ACK (up to 3 retries)."""
        fin_pkt = Packet(seq_num=self.next_seq, flags=FIN)
        for _ in range(3):
            self.sock.send(fin_pkt, self.dest_addr)
            ack_pkt, _ = self.sock.receive(timeout=self._timeout)
            if ack_pkt is not None and ack_pkt.is_valid() and ack_pkt.has_flag(ACK):
                return
        # Best-effort: if no FIN-ACK arrives after retries, proceed with teardown

    def _effective_window(self) -> int:
        """Window size in packets, incorporating congestion control when available."""
        try:
            if self._congestion is not None:
                return min(self.window, self._congestion.window)
        except NotImplementedError:
            pass
        return self.window

    def _remaining_timeout(self) -> float:
        """Seconds left before the oldest in-flight packet times out."""
        if self._timer_start is None:
            return self._timeout
        elapsed = time.time() - self._timer_start
        return max(0.0, self._timeout - elapsed)

    def _notify_congestion_ack(self) -> None:
        try:
            if self._congestion is not None:
                self._congestion.on_ack()
        except NotImplementedError:
            pass

    def _notify_congestion_timeout(self) -> None:
        try:
            if self._congestion is not None:
                self._congestion.on_timeout()
        except NotImplementedError:
            pass


# ----------------------------------------------------------------------
# Manual smoke test: send a file to a running receiver
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    host = constants.LOCALHOST
    port = 9000

    if len(sys.argv) >= 2:
        filepath = sys.argv[1]
        with open(filepath, "rb") as f:
            payload = f.read()
    else:
        payload = b"Hello from the Anti-Hackers RDT sender!\n" * 50

    print(f"Sending {len(payload)} bytes to {host}:{port} ...")
    sender = Sender(dest_addr=(host, port))
    sender.send(payload)
    sender.close()
    print("Done.")
