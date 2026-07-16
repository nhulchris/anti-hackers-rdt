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

	print("Round Trip Times: ")
	for i in range(1, len(sender.allRoundTripTimes)):
		print(sender.allRoundTripTimes[i])
		averageRoundTripTime += sender.allRoundTripTimes[i]

	averageRoundTripTime /= len(sender.allRoundTripTimes)

	print("\nAverage Round Trip Time: ")
	print(averageRoundTripTime)
	print()

	print("Number of Retransmissions: ")
	print(sender.numberOfRetransmissions)
	print()

	print("Total Transmission Time:")
	print(sender.totalTransmissionTime)
	print()

	print("Total bytes sent:")
	print(sender.totalBytesSent)
	print()

	throughput = sender.totalBytesSent/sender.totalTransmissionTime

	print("Throughput:")
	print(f"{int(throughput)} bytes/sec")
	print()