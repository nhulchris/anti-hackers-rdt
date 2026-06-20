"""
receiver.py -- Reliable receiver (Task 3: Chris Nhul).

Responsible for:
  - receiving DATA packets and verifying their checksum
  - delivering bytes to the application in order
  - discarding duplicates and (for Selective Repeat) buffering out-of-order packets
  - generating ACKs (cumulative to start; selective later if time allows)
  - advertising the receive window (flow control)

Coordinate the ACK format with Theo (Task 2) -- your ack_num is what advances his window.
"""

from socket_layer import UDPSocket
from packet import Packet, ACK
import constants


class Receiver:
    def __init__(self, bind_addr):
        self.sock = UDPSocket(bind_addr)
        self.expected_seq = 0      # next in-order sequence number we want
        self.buffer = {}           # out-of-order holding area: seq -> payload

    def receive(self, output_stream=None):
        """
        Receive loop.

        TODO (Chris):
          1. recv a packet; if not packet.is_valid(), drop it (corrupted).
          2. If seq == expected_seq: deliver the payload, advance expected_seq,
             then flush any buffered packets that are now in order.
          3. If it's a duplicate / old packet: re-send the ACK.
          4. If it's ahead of expected_seq: buffer it (Selective Repeat) or drop it (Go-Back-N).
          5. Send an ACK with the cumulative ack_num and the current advertised window.
          6. Stop when the FIN packet arrives and everything is delivered.
        """
        raise NotImplementedError("Chris: implement the receive + ACK loop")

    def _send_ack(self, addr):
        """TODO (Chris): build and send an ACK packet with ack_num = self.expected_seq."""
        raise NotImplementedError

    def close(self):
        self.sock.close()


if __name__ == "__main__":
    # TODO (Chris): a small manual test, e.g. listen and write received bytes to a file.
    pass
