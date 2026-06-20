"""
socket_layer.py -- Thin UDP wrapper for the Anti-Hackers RDT protocol.

Task 1 (Max Anderson). Wraps a UDP socket so the sender and receiver can send and
receive Packet objects without touching raw bytes directly.
"""

import socket
from packet import Packet

MAX_DATAGRAM = 65535


class UDPSocket:
    def __init__(self, bind_addr=None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if bind_addr is not None:
            self.sock.bind(bind_addr)

    def send(self, packet: Packet, addr):
        """Serialize and send a Packet to addr (host, port)."""
        self.sock.sendto(packet.pack(), addr)

    def receive(self, timeout=None):
        """
        Wait (optionally up to `timeout` seconds) for one datagram.
        Returns (Packet, addr), or (None, None) on timeout.
        """
        self.sock.settimeout(timeout)
        try:
            raw, addr = self.sock.recvfrom(MAX_DATAGRAM)
        except socket.timeout:
            return None, None
        return Packet.unpack(raw), addr

    def close(self):
        self.sock.close()
