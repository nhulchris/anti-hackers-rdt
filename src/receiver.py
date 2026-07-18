"""
receiver.py -- Reliable receiver (Task 3: Chris Nhul).

Go-Back-N receiver: accepts packets strictly in order, delivers their payload to the
application, discards duplicates / out-of-order / corrupted packets, and replies to
every packet with a CUMULATIVE ACK.

ACK convention (coordinate this with Theo / Task 2):
    ack_num = self.expected_seq = "the next sequence number I still need"
    i.e. "I have received everything below ack_num; send me ack_num next."
    Theo's sender slides its window so that base = ack_num.

Build order: this is the Phase-1 deliverable. The Phase-2 upgrade (Selective Repeat
buffering + real flow control) is sketched at the bottom of this file.
"""

from socket_layer import UDPSocket
from packet import Packet, ACK, FIN, DATA
import constants
import random

class Receiver:
    def __init__(self, bind_addr=None):
        # bind_addr is optional so the protocol logic can be unit-tested without a socket.
        self.sock = UDPSocket(bind_addr) if bind_addr is not None else None
        self.expected_seq = 0                       # next in-order seq we want
        self.advertised_window = constants.DEFAULT_WINDOW

        #for testing
        self.totalPayloadReceived = 0

    # ---- pure protocol logic (no sockets -> easy to unit-test) ----
    def process(self, pkt: Packet):
        """
        Handle one incoming packet.

        Returns (delivered, ack_packet, done):
          delivered    : bytes handed to the application this step (b"" if none)
          ack_packet   : the ACK Packet to send back to the sender
          done         : True if this was the FIN (transfer complete)
        """
        # 1. Corrupted -> drop the payload, but re-ACK so the sender knows where we are.
        if not pkt.is_valid():
            return b"", self._build_ack(), False

        # 2. End of transfer.
        if pkt.has_flag(FIN):
            return b"", self._build_ack(fin=True), True

        # 3. DATA. Only the exact next-in-order packet is accepted (Go-Back-N).
        delivered = b""
        if pkt.has_flag(DATA) and pkt.seq_num == self.expected_seq:
            delivered = pkt.payload
            self.expected_seq += 1

        # Duplicates (seq < expected) and gaps (seq > expected) fall through:
        # we deliver nothing and just re-ACK the cumulative point.

        return delivered, self._build_ack(), False

    def _build_ack(self, fin=False) -> Packet:
        flags = ACK | (FIN if fin else 0)
        return Packet(ack_num=self.expected_seq, flags=flags,
                      window=self.advertised_window)

    # ---- socket loop (used in real runs) ----
    def receive(self, output_stream=None) -> bytes:
        """
        Receive a full transfer and return the assembled bytes. If output_stream is a
        writable binary file, payloads are also written to it as they arrive. Stops on FIN.
        """
        assert self.sock is not None, "Receiver needs a bind_addr to use receive()"
        data = bytearray()
        while True:
            pkt, addr = self.sock.receive(timeout=None)

            print(
                f"(In receiver) Got packet: "
                f"seq={pkt.seq_num}, "
                f"ack={pkt.ack_num}, "
                f"flags={pkt.flags}, "
                f"payload_len={len(pkt.payload)}"
            )

            if pkt.payload:
                try:
                    print(f"(In receiver)Message: {pkt.payload.decode('utf-8')}")
                except UnicodeDecodeError:
                    print(f"Raw bytes: {pkt.payload}")
            
            if pkt is None:
                continue
            delivered, ack, done = self.process(pkt)

            if delivered:
                print(f"*** (In receiver) Packet received! Seq Num: {pkt.seq_num} ***")
                
                self.totalPayloadReceived += len(delivered)

                data.extend(delivered)
                if output_stream is not None:
                    output_stream.write(delivered)

            if ack is not None:
                if random.random() < constants.ACK_LOSS_PROBABILITY:
                    print(f"*** Simulating lost ACK {ack.ack_num} ***")
                    # Do NOT send the ACK
                    continue
                
            print(f"(In receiver) Sending ACK {ack.ack_num}")
            self.sock.send(ack, addr)

            if done:
                break
        return bytes(data)

    def close(self):
        if self.sock is not None:
            self.sock.close()


if __name__ == "__main__":
    # Simple manual run: listen on localhost:9000 and write the transfer to a file.
    rcv = Receiver((constants.LOCALHOST, 9000))
    print("Receiver listening on", constants.LOCALHOST, "port 9000 ...")
    with open("received_output.dat", "wb") as f:
        total = rcv.receive(output_stream=f)
    print(f"Transfer complete: {len(total)} bytes written to received_output.dat")
    rcv.close()


# -----------------------------------------------------------------------------
# PHASE 2 UPGRADE -- Selective Repeat + flow control (your next task, Chris):
#   * Add  self.buffer = {}  (seq -> payload) for out-of-order packets.
#   * In process(): if seq == expected_seq, deliver it, then while (expected_seq in
#     self.buffer) deliver buffered packets and pop them, advancing expected_seq.
#     If seq > expected_seq and within the window, store it in self.buffer (don't drop).
#   * Make advertised_window reflect real free buffer space:
#     self.advertised_window = MAX_BUFFER - len(self.buffer)
#   * Coordinate with Theo so the sender only retransmits the specific lost packet
#     instead of the whole window.
# -----------------------------------------------------------------------------
