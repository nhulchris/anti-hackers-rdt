"""
test_receiver.py -- unit tests for the Go-Back-N receiver. Run with: pytest

These drive Receiver.process() directly with crafted packets, so no sockets are needed.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from packet import Packet, DATA, FIN  # noqa: E402
from receiver import Receiver  # noqa: E402


def data_pkt(seq, payload):
    return Packet.unpack(Packet(seq_num=seq, flags=DATA, payload=payload).pack())


def test_in_order_delivery():
    r = Receiver()
    d0, ack0, done0 = r.process(data_pkt(0, b"AA"))
    d1, ack1, done1 = r.process(data_pkt(1, b"BB"))
    assert d0 == b"AA" and d1 == b"BB"
    assert not done0 and not done1
    assert r.expected_seq == 2
    assert ack1.ack_num == 2          # cumulative: "send me packet 2 next"


def test_duplicate_is_dropped():
    r = Receiver()
    r.process(data_pkt(0, b"AA"))
    delivered, ack, _ = r.process(data_pkt(0, b"AA"))   # same packet again
    assert delivered == b""           # not delivered twice
    assert ack.ack_num == 1           # still expecting 1


def test_out_of_order_is_dropped():
    r = Receiver()
    r.process(data_pkt(0, b"AA"))
    delivered, ack, _ = r.process(data_pkt(2, b"CC"))   # gap: 1 is missing
    assert delivered == b""           # Go-Back-N drops the gap packet
    assert r.expected_seq == 1
    assert ack.ack_num == 1           # re-ACK the cumulative point


def test_corrupted_is_dropped():
    r = Receiver()
    raw = bytearray(Packet(seq_num=0, flags=DATA, payload=b"AA").pack())
    raw[-1] ^= 0xFF                   # corrupt the payload
    delivered, ack, _ = r.process(Packet.unpack(bytes(raw)))
    assert delivered == b""
    assert r.expected_seq == 0        # nothing accepted


def test_fin_ends_transfer():
    r = Receiver()
    delivered, ack, done = r.process(Packet.unpack(Packet(flags=FIN).pack()))
    assert done is True
    assert ack.has_flag(FIN)
