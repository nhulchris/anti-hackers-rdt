"""
test_sender.py -- unit tests for the Go-Back-N sender. Run with: pytest

These use a FakeSocket instead of the network, so we can script exactly which ACKs
arrive (or don't) and observe what the sender transmits in response.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import constants  # noqa: E402
from packet import Packet, ACK, DATA, FIN  # noqa: E402
import sender as sender_module  # noqa: E402
from sender import Sender  # noqa: E402


class FakeSocket:
    """Stands in for UDPSocket: records sends, replays a scripted list of replies."""

    def __init__(self, replies=None):
        self.sent = []                  # every Packet the sender transmitted
        self.replies = list(replies or [])

    def send(self, packet, addr):
        self.sent.append(packet)

    def receive(self, timeout=None):
        if self.replies:
            return self.replies.pop(0), ("127.0.0.1", 9000)
        return None, None               # behaves like a timeout

    def close(self):
        pass


def ack(n):
    """A valid ACK packet as the receiver would build it (round-tripped for checksum)."""
    return Packet.unpack(Packet(ack_num=n, flags=ACK).pack())


def make_sender(replies):
    s = Sender(dest_addr=("127.0.0.1", 9000))
    s.sock.close()                      # discard the real socket
    s.sock = FakeSocket(replies)
    s._timeout = 0.05                   # keep timeout-path tests fast
    return s


def data_packets(fake):
    return [p for p in fake.sent if p.has_flag(DATA)]


def test_small_payload_single_packet_and_fin():
    payload = b"x" * 100                # fits in one packet
    s = make_sender([ack(1), ack(1)])   # ACK the data, then ACK the FIN
    s.send(payload)

    datas = data_packets(s.sock)
    assert len(datas) == 1
    assert datas[0].seq_num == 0
    assert datas[0].payload == payload
    assert any(p.has_flag(FIN) for p in s.sock.sent)


def test_payload_is_chunked_and_reassembles():
    payload = b"A" * (constants.PAYLOAD_SIZE * 2 + 10)   # 3 packets
    # ACK one at a time, like a real receiver (window starts at 1 in slow start).
    s = make_sender([ack(1), ack(2), ack(3), ack(3)])
    s.send(payload)

    datas = data_packets(s.sock)
    assert [p.seq_num for p in datas] == [0, 1, 2]
    assert b"".join(p.payload for p in datas) == payload


def test_cumulative_ack_slides_base():
    payload = b"B" * (constants.PAYLOAD_SIZE * 3)        # 3 packets
    # First ACK opens the window (slow start); one cumulative ack(3) then
    # confirms the remaining two packets at once.
    s = make_sender([ack(1), ack(3), ack(3)])
    s.send(payload)
    assert s.base == 3
    assert s._unacked == {}             # nothing left in flight


class TimeoutThenAcks(FakeSocket):
    """None in the script simulates a timeout; anything else is delivered."""

    def receive(self, timeout=None):
        r = self.replies.pop(0) if self.replies else None
        return (r, ("127.0.0.1", 9000)) if r is not None else (None, None)


def test_timeout_triggers_retransmission():
    payload = b"C" * constants.PAYLOAD_SIZE             # 1 packet in flight (cwnd=1)
    s = make_sender([])
    # Timeout first -> Go-Back-N resends the in-flight packet -> then ACKs arrive.
    s.sock = TimeoutThenAcks([None, ack(1), ack(1)])
    s.send(payload)

    datas = data_packets(s.sock)
    assert [p.seq_num for p in datas] == [0, 0]          # original + retransmission
    assert s.numberOfRetransmissions == 1


def test_stale_duplicate_ack_does_not_move_base():
    payload = b"D" * (constants.PAYLOAD_SIZE * 2)
    s = make_sender([ack(1), ack(1), ack(2), ack(2)])    # dup ack(1) in the middle
    s.send(payload)
    assert s.base == 2                  # finished correctly despite the duplicate


def test_zero_length_payload_sends_only_fin():
    s = make_sender([ack(0)])
    s.send(b"")
    assert data_packets(s.sock) == []
    assert any(p.has_flag(FIN) for p in s.sock.sent)
