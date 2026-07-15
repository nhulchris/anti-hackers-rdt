import os
import sys
import constants
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from packet import Packet, DATA, FIN  # noqa: E402
from receiver import Receiver  # noqa: E402
from sender import Sender


#A simulation of our protocol, with 1000 packets.
#Tracks the metrics as required in the README.md
## Metrics to collect
# - Throughput and goodput
# - Number of retransmissions
# - Transfer completion time
# - (compare against a raw-UDP and a TCP baseline)

def start_sender():
    import sys

    host = constants.LOCALHOST
    port = 9000

    sender = Sender(dest_addr=(host, port))
    return sender

def start_receiver():
    rcv = Receiver((constants.LOCALHOST, 9000))
    print("Receiver listening...")

    try:
        rcv.receive()
    finally:
        rcv.close()

def run_simulation():
	receiver_thread = threading.Thread(target=start_receiver)
	receiver_thread.start()

	# Give receiver time to bind to the port
	time.sleep(0.5)

	sender = start_sender()

	for seq in range(1000):
	    pkt = Packet(
	        seq_num=seq,
	        ack_num=0,
	        flags=DATA,
	        payload=f"Packet {seq}".encode()
	    )

	    sender.sock.send(pkt, sender.dest_addr)

	sender.close()

	receiver_thread.join()


run_simulation();