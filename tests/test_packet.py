"""
test_packet.py -- unit tests for the packet format. Run with: pytest

These pass against the provided src/packet.py and are a template for the tests the
other members should write (test_sender.py, test_receiver.py, test_congestion.py).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from packet import Packet, DATA, HEADER_SIZE  # noqa: E402


def test_pack_unpack_roundtrip():
    pkt = Packet(seq_num=42, ack_num=7, flags=DATA, window=10, payload=b"hello")
    out = Packet.unpack(pkt.pack())
    assert out.seq_num == 42
    assert out.ack_num == 7
    assert out.has_flag(DATA)
    assert out.window == 10
    assert out.payload == b"hello"


def test_valid_checksum_passes():
    pkt = Packet(seq_num=1, payload=b"clean data")
    assert Packet.unpack(pkt.pack()).is_valid()


def test_checksum_detects_corruption():
    pkt = Packet(seq_num=1, payload=b"data")
    raw = bytearray(pkt.pack())
    raw[-1] ^= 0xFF  # flip the bits of the last payload byte
    assert not Packet.unpack(bytes(raw)).is_valid()


def test_header_size_is_15():
    assert HEADER_SIZE == 15
