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
        """
        TODO (Neha):
          - slow start: cwnd += 1 per ACK, until cwnd >= ssthresh (then switch state)
          - congestion avoidance: cwnd += 1/cwnd per ACK (additive increase)
        """
        raise NotImplementedError

    def on_timeout(self):
        """TODO (Neha): ssthresh = max(cwnd / 2, 1); cwnd = 1; state = 'slow_start'."""
        raise NotImplementedError

    def on_triple_dup_ack(self):
        """TODO (Neha, stretch goal): fast retransmit / fast recovery."""
        raise NotImplementedError

    @property
    def window(self) -> int:
        """Whole-packet window the sender can use."""
        return max(1, int(self.cwnd))
