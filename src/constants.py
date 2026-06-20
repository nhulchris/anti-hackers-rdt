"""
constants.py -- Shared configuration the whole team agrees on.

Task 1 (Max Anderson) owns this file; the other modules import their values from here
so everyone uses the same numbers.
"""

PAYLOAD_SIZE = 1024        # max bytes of application data per packet
DEFAULT_WINDOW = 10        # initial window size (in packets)
DEFAULT_TIMEOUT = 0.5      # retransmission timeout in seconds (Task 2 may refine with RTT estimation)
LOCALHOST = "127.0.0.1"
