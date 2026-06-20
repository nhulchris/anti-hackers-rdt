"""
sender.py -- Reliable sender (Task 2: Theophilus Cox).

Responsible for:
  - breaking application data into packets
  - the sliding window
  - sequence numbering
  - retransmission timers / timeout handling
  - processing incoming ACKs

Build order: get stop-and-wait working first (send one packet, wait for its ACK,
retransmit on timeout), THEN grow it into a sliding window. The congestion window
from Task 4 (Neha) plugs in where marked below.

Coordinate the ACK format with Chris (Task 3) -- his ack_num is what advances your window.
"""

from socket_layer import UDPSocket
from packet import Packet, DATA, ACK
import constants


class Sender:
    def __init__(self, dest_addr, bind_addr=None):
        self.sock = UDPSocket(bind_addr)
        self.dest_addr = dest_addr
        self.base = 0          # oldest unacked sequence number
        self.next_seq = 0      # next sequence number to assign
        self.window = constants.DEFAULT_WINDOW
        # TODO (Task 4 integration): replace the fixed window above with the
        #   congestion window from congestion.CongestionControl.

    def send(self, data: bytes):
        """
        Reliably send `data` to the receiver.

        TODO (Theo):
          1. Split `data` into PAYLOAD_SIZE chunks -> Packets with the DATA flag.
          2. Send all packets that fit in the window; start a timer for the oldest unacked.
          3. On ACK (see _handle_ack): slide the window forward.
          4. On timeout: retransmit (Go-Back-N resends the window; Selective Repeat
             resends only the lost packet).
          5. Finish with a FIN once everything is acknowledged.
        """
        raise NotImplementedError("Theo: implement the sliding-window send loop")

    def _handle_ack(self, packet: Packet):
        """TODO (Theo): advance self.base based on the cumulative ack_num."""
        raise NotImplementedError

    def close(self):
        self.sock.close()


if __name__ == "__main__":
    # TODO (Theo): a small manual test, e.g. send a file to a running receiver.
    pass
