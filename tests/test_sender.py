"""
test_sender.py -- unit tests for the sliding-window sender. Run with: pytest

Tests drive Sender's internal logic with a fake socket so no real network I/O
occurs, mirroring the approach used in test_receiver.py for Receiver.process().
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import constants  # noqa: E402
from congestion import CongestionControl  # noqa: E402
from packet import Packet, ACK, DATA, FIN  # noqa: E402
from sender import Sender  # noqa: E402


class FakeSocket:
    """Stand-in for UDPSocket: captures outgoing packets and returns canned ACKs."""

    def __init__(self, responses=None):
        self.sent = []                          # list of (Packet, addr)
        self._responses = list(responses or []) # list of (Packet|None, addr|None)

    def send(self, packet, addr):
        self.sent.append((packet, addr))

    def receive(self, timeout=None):
        if self._responses:
            return self._responses.pop(0)
        return None, None

    def close(self):
        pass


def _make_sender(responses=None):
    """Create a Sender backed by a FakeSocket; no real UDP socket is used."""
    s = Sender(dest_addr=("127.0.0.1", 9000))
    s.sock = FakeSocket(responses or [])
    return s


def _ack(ack_num):
    """Return a (Packet, addr) tuple for use as a FakeSocket canned response."""
    return Packet.unpack(Packet(ack_num=ack_num, flags=ACK).pack()), ("127.0.0.1", 9000)


def _finack():
    """FIN-ACK response, matching what the real receiver sends (ACK | FIN)."""
    return Packet.unpack(Packet(flags=ACK | FIN).pack()), ("127.0.0.1", 9000)


# ---- _handle_ack (pure state logic) ----

def test_handle_ack_advances_base():
    s = _make_sender()
    s._unacked[0] = Packet(seq_num=0, flags=DATA, payload=b"A")
    s.base = 0
    s.next_seq = 1
    s._timer_start = 0.0

    s._handle_ack(Packet.unpack(Packet(ack_num=1, flags=ACK).pack()))

    assert s.base == 1
    assert 0 not in s._unacked


def test_handle_ack_clears_entire_window_and_stops_timer():
    s = _make_sender()
    for i in range(3):
        s._unacked[i] = Packet(seq_num=i, flags=DATA, payload=b"X")
    s.base = 0
    s.next_seq = 3
    s._timer_start = 0.0

    s._handle_ack(Packet.unpack(Packet(ack_num=3, flags=ACK).pack()))

    assert s.base == 3
    assert s._unacked == {}
    assert s._timer_start is None   # no packets in flight: timer stopped


def test_handle_ack_restarts_timer_when_packets_still_in_flight():
    s = _make_sender()
    for i in range(3):
        s._unacked[i] = Packet(seq_num=i, flags=DATA, payload=b"X")
    s.base = 0
    s.next_seq = 3
    s._timer_start = 0.0

    # ACK only the first packet; two remain in flight
    s._handle_ack(Packet.unpack(Packet(ack_num=1, flags=ACK).pack()))

    assert s.base == 1
    assert 0 not in s._unacked
    assert s._timer_start is not None   # timer restarted for remaining packets


def test_duplicate_ack_is_ignored():
    s = _make_sender()
    s._unacked[0] = Packet(seq_num=0, flags=DATA, payload=b"A")
    s.base = 2
    s.next_seq = 3
    s._timer_start = 0.0

    # ack_num=1 is below base=2 -- stale ACK
    s._handle_ack(Packet.unpack(Packet(ack_num=1, flags=ACK).pack()))

    assert s.base == 2          # unchanged
    assert 0 in s._unacked      # nothing cleared


# ---- _retransmit ----

def test_retransmit_resends_all_unacked_in_order():
    s = _make_sender()
    for i in range(3):
        s._unacked[i] = Packet(seq_num=i, flags=DATA, payload=f"p{i}".encode())
    s.base = 0
    s.next_seq = 3

    s._retransmit()

    sent_seqs = [p.seq_num for p, _ in s.sock.sent]
    assert sent_seqs == [0, 1, 2]


def test_retransmit_increments_counter_each_call():
    s = _make_sender()
    s._unacked[0] = Packet(seq_num=0, flags=DATA, payload=b"A")
    s.base = 0
    s.next_seq = 1

    s._retransmit()
    s._retransmit()

    assert s.numberOfRetransmissions == 2


# ---- _effective_window ----

def test_effective_window_without_congestion_returns_sender_window():
    s = _make_sender()
    s._congestion = None
    s.window = 7
    assert s._effective_window() == 7


def test_effective_window_congestion_is_the_bottleneck():
    s = _make_sender()
    s.window = 10
    cc = CongestionControl()
    cc.cwnd = 3.0
    s._congestion = cc
    assert s._effective_window() == 3


def test_effective_window_sender_window_is_the_bottleneck():
    s = _make_sender()
    s.window = 2
    cc = CongestionControl()
    cc.cwnd = 20.0
    s._congestion = cc
    assert s._effective_window() == 2


# ---- send() end-to-end ----

def test_send_empty_data_sends_only_fin():
    s = _make_sender([_finack()])  # FIN-ACK

    s.send(b"")

    data_pkts = [p for p, _ in s.sock.sent if p.has_flag(DATA)]
    fin_pkts  = [p for p, _ in s.sock.sent if p.has_flag(FIN)]
    assert data_pkts == []
    assert len(fin_pkts) >= 1


def test_send_single_chunk_delivers_payload_and_fin():
    s = _make_sender([_ack(1), _finack()])  # data ACK, then FIN-ACK

    s.send(b"hello world")

    data_pkts = [p for p, _ in s.sock.sent if p.has_flag(DATA)]
    fin_pkts  = [p for p, _ in s.sock.sent if p.has_flag(FIN)]
    assert len(data_pkts) == 1
    assert data_pkts[0].payload == b"hello world"
    assert len(fin_pkts) >= 1


def test_send_multiple_chunks_reassembles_correctly():
    payload = b"Z" * (constants.PAYLOAD_SIZE * 3)
    responses = [_ack(1), _ack(2), _ack(3), _finack()]  # 3 data ACKs + FIN-ACK
    s = _make_sender(responses)

    s.send(payload)

    data_pkts = [p for p, _ in s.sock.sent if p.has_flag(DATA)]
    assert len(data_pkts) == 3
    assert b"".join(p.payload for p in data_pkts) == payload


def test_fin_not_confirmed_by_stale_data_ack():
    # A leftover cumulative data ACK (ACK flag only) must NOT be mistaken for the
    # FIN-ACK; otherwise the sender tears down while its FIN may have been lost and
    # the receiver is still waiting. The sender should keep resending the FIN.
    s = _make_sender([_ack(1), _ack(5), _ack(5)])  # data ACK, then only stale data ACKs

    s.send(b"hello world")

    fin_pkts = [p for p, _ in s.sock.sent if p.has_flag(FIN)]
    assert len(fin_pkts) == 3  # retried the full 3 times, never falsely confirmed


def test_timeout_triggers_retransmission():
    # cwnd starts at 1, so exactly one packet is in flight. A (None, None) response
    # simulates a timeout -> Go-Back-N resends the in-flight packet -> then the ACK
    # arrives and the transfer completes. (Ported from the origin/main suite.)
    payload = b"C" * constants.PAYLOAD_SIZE
    s = _make_sender([(None, None), _ack(1), _finack()])

    s.send(payload)

    data_pkts = [p for p, _ in s.sock.sent if p.has_flag(DATA)]
    assert [p.seq_num for p in data_pkts] == [0, 0]   # original + retransmission
    assert s.numberOfRetransmissions == 1


def test_send_tracks_bytes_sent():
    s = _make_sender([_ack(1), _finack()])

    s.send(b"abc")

    assert s.totalBytesSent > 0
