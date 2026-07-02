# Anti-Hackers RDT

A reliable data transfer protocol built on top of UDP, in Python.
ICS 460-50 (Networks and Security), Summer 2026 -- Term Project, Option 1 (Hands-On Implementation).

## What it does
Implements TCP-like reliability over UDP from scratch: a sliding window, acknowledgements,
retransmission timers, and AIMD congestion control. We then evaluate it under injected
packet loss and delay using a `tc`/`netem` testbed.

## Team and task assignments
| Task | Owner | Files |
|------|-------|-------|
| 1 -- Packet format + socket layer + project setup | Max Anderson | `src/packet.py`, `src/socket_layer.py`, `src/constants.py` |
| 2 -- Sender (sliding window, retransmission) | Theophilus Cox (leader) | `src/sender.py` |
| 3 -- Receiver (buffering, ACKs, flow control) | Chris Nhul | `src/receiver.py` |
| 4 -- Congestion control + evaluation / testbed | Neha Virani | `src/congestion.py`, `eval/` |

## Repository layout
```
anti-hackers-rdt/
|- README.md
|- requirements.txt
|- .gitignore
|- src/
|  |- packet.py         # Task 1 -- packet format + checksum (DONE: starter provided)
|  |- socket_layer.py   # Task 1 -- UDP send/recv wrapper (DONE: starter provided)
|  |- constants.py      # Task 1 -- shared config
|  |- sender.py         # Task 2 -- DONE (Go-Back-N sliding window, retransmission, ACK processing)
|  |- receiver.py       # Task 3 -- TODO
|  |- congestion.py     # Task 4 -- TODO
|- tests/
|  |- test_packet.py    # passes; template for the other tests
|- eval/
|  |- setup_netem.sh    # Task 4 -- loss/delay testbed
|  |- run_experiments.py# Task 4 -- TODO
|  |- README.md
|- docs/
   |- progress_report_1.md
```

## Setup
1. Clone the repo (or open it in GitHub Desktop).
2. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Running
The modules live in `src/`. Run scripts from inside that folder so imports resolve:
```
cd src
python receiver.py     # (once implemented) start the receiver
python sender.py       # (once implemented) start the sender
```

## Testing
```
pytest
```
`tests/test_packet.py` already passes against the provided packet format -- use it as a
template for `test_sender.py`, `test_receiver.py`, and `test_congestion.py`.

## Branching workflow
- `main` always runs. Nobody commits directly to `main`.
- Each member works on a branch named for their task (`sender`, `receiver`, `congestion`,
  `eval`), pushes it, and opens a Pull Request. The leader reviews and merges.
- Track work on the GitHub Projects board: Todo -> In Progress -> In Review -> Done.

## Build order
Get a dead-simple version working end-to-end first: packet format -> stop-and-wait
sender/receiver -> confirm a file transfers correctly -> then add the sliding window,
flow control, and congestion control.

## Note on tooling
Initial project scaffolding (structure, this README, the packet format, and the module
skeletons) was generated with AI assistance and then reviewed and implemented by the team,
consistent with the course policy on generative AI use.
