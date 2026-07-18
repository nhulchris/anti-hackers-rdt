"""
congestion.py -- Congestion control (Task 4: Neha Virani).

A simple TCP-style controller the Sender (Task 2) consults to decide how many packets
may be in flight. Implements slow start + AIMD congestion avoidance, with fast
retransmit/recovery as a stretch goal.

Coordinate with Theo: the Sender calls on_ack() / on_timeout() and reads `window`.
"""


class CongestionControl:
    def __init__(self):
        self.cwnd = 1.0            # congestion window (in packets)
        self.ssthresh = 64         # slow-start threshold
        self.state = "slow_start"  # "slow_start" or "congestion_avoidance"

    def on_ack(self):
        """Increase the congestion window after a new cumulative ACK."""
        if self.state == "slow_start":
            # Slow start grows by roughly one window per round trip.
            self.cwnd += 1.0
            if self.cwnd >= self.ssthresh:
                self.state = "congestion_avoidance"
        else:
            # Adding 1/cwnd for every ACK grows cwnd by about one packet per RTT.
            self.cwnd += 1.0 / self.cwnd

    def on_timeout(self):
        """React to packet loss detected by the retransmission timer."""
        self.ssthresh = max(self.cwnd / 2.0, 1.0)
        self.cwnd = 1.0
        self.state = "slow_start"

    def on_triple_dup_ack(self):
        """Reduce the window without returning all the way to slow start."""
        self.ssthresh = max(self.cwnd / 2.0, 1.0)
        self.cwnd = self.ssthresh
        self.state = "congestion_avoidance"

    @property
    def window(self) -> int:
        """Whole-packet window the sender can use."""
        return max(1, int(self.cwnd))
