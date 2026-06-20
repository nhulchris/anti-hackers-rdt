"""
packet.py -- Packet format and (de)serialization for the Anti-Hackers RDT protocol.

Task 1 (Max Anderson): the shared foundation. Every other module imports from here,
so the header layout and the Packet API should be agreed by the whole group before
sender/receiver/congestion build on it.

Header layout (15 bytes, network byte order):
    seq_num   : uint32  (4)  - sequence number of this packet
    ack_num   : uint32  (4)  - cumulative ACK number
    flags     : uint8   (1)  - bitmask: SYN | ACK | FIN | DATA
    window    : uint16  (2)  - receiver's advertised window (flow control)
    length    : uint16  (2)  - number of payload bytes
    checksum  : uint16  (2)  - 16-bit Internet checksum over header + payload
"""

import struct

# ---- Header definition ----
HEADER_FORMAT = "!IIBHHH"                      # ! = network (big-endian)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)   # 15 bytes

# ---- Flag bits ----
SYN = 0b0001
ACK = 0b0010
FIN = 0b0100
DATA = 0b1000


def checksum(data: bytes) -> int:
    """16-bit one's-complement Internet checksum (RFC 1071 style)."""
    if len(data) % 2:
        data += b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) + data[i + 1]
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


class Packet:
    def __init__(self, seq_num=0, ack_num=0, flags=0, window=0, payload=b""):
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.flags = flags
        self.window = window
        self.payload = payload
        self._received_checksum = None

    def pack(self) -> bytes:
        """Serialize to bytes, computing the checksum over header + payload."""
        length = len(self.payload)
        header_zero_cksum = struct.pack(
            HEADER_FORMAT, self.seq_num, self.ack_num, self.flags,
            self.window, length, 0,
        )
        cksum = checksum(header_zero_cksum + self.payload)
        header = struct.pack(
            HEADER_FORMAT, self.seq_num, self.ack_num, self.flags,
            self.window, length, cksum,
        )
        return header + self.payload

    @classmethod
    def unpack(cls, raw: bytes) -> "Packet":
        """Parse bytes back into a Packet (does not raise on a bad checksum)."""
        seq, ack, flags, window, length, cksum = struct.unpack(
            HEADER_FORMAT, raw[:HEADER_SIZE]
        )
        payload = raw[HEADER_SIZE:HEADER_SIZE + length]
        pkt = cls(seq, ack, flags, window, payload)
        pkt._received_checksum = cksum
        return pkt

    def is_valid(self) -> bool:
        """Recompute the checksum and compare with the one we received."""
        length = len(self.payload)
        header_zero_cksum = struct.pack(
            HEADER_FORMAT, self.seq_num, self.ack_num, self.flags,
            self.window, length, 0,
        )
        return checksum(header_zero_cksum + self.payload) == self._received_checksum

    def has_flag(self, flag) -> bool:
        return bool(self.flags & flag)

    def __repr__(self):
        names = [n for n, v in (("SYN", SYN), ("ACK", ACK), ("FIN", FIN), ("DATA", DATA))
                 if self.flags & v]
        return (f"<Packet seq={self.seq_num} ack={self.ack_num} "
                f"flags={'|'.join(names) or '0'} len={len(self.payload)}>")
