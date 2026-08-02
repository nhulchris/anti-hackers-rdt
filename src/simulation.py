import os
import sys
import constants
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from packet import Packet, DATA, FIN  # noqa: E402

#A simulation of our protocol, with 1000 packets.
#Tracks the metrics as required in the README.md
## Metrics to collect
# - Throughput and goodput
# - Number of retransmissions
# - Transfer completion time
# - (compare against a raw-UDP and a TCP baseline)

def output_simulation_details(sender):
	print("\n\nSimulation Details")
	print("---------------------")

	averageRoundTripTime = 0
	throughput = 0

	print("Round Trip Times:")
	for i in range(1, len(sender.allRoundTripTimes)):
		rtt = sender.allRoundTripTimes[i]
		print(f"  {rtt * 1000:9.2f} ms")
		averageRoundTripTime += rtt

	averageRoundTripTime /= len(sender.allRoundTripTimes)

	print("\nAverage Round Trip Time:")
	print(f"  {averageRoundTripTime * 1000:.2f} ms  ({averageRoundTripTime:.4f} s)")
	print()

	print("Number of Retransmissions:")
	print(f"  {sender.numberOfRetransmissions} packets")
	print()

	print("Total Transmission Time:")
	print(f"  {sender.totalTransmissionTime:.3f} s")
	print()

	print("Total bytes sent:")
	print(f"  {sender.totalBytesSent:,} bytes")
	print()

	throughput = sender.totalBytesSent/sender.totalTransmissionTime

	print("Throughput:")
	print(f"  {int(throughput):,} bytes/sec  ({throughput * 8 / 1_000_000:.2f} Mbps)")
	print()
