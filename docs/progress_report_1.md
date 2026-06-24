# Progress Report 1 -- The Anti-Hackers

**Project:** Reliable Transport Protocol over UDP
**Course:** ICS 460-50, Networks and Security -- Summer 2026
**Date:** June 23, 2026
**Repository:** https://github.com/nhulchris/anti-hackers-rdt

## Completion: ~40%

## What's done
- (Max / Task 1 -- foundation) `packet.py`, `socket_layer.py`, and `constants.py` are complete. The 15-byte header (seq, ack, flags, window, length, checksum) is defined in `packet.py` with full pack/unpack/checksum validation (RFC 1071). `UDPSocket` in `socket_layer.py` wraps the raw socket so the rest of the team works with `Packet` objects, not bytes. `tests/test_packet.py` has 4 passing unit tests covering round-trip serialization, checksum validation, and corruption detection.
- (Theo / Task 2 -- sender) `sender.py` skeleton is in place: `Sender.__init__` sets up the UDP socket, sequence tracking (`base`, `next_seq`), and a fixed window pulled from `constants`. The `send()` and `_handle_ack()` stubs are stubbed with `NotImplementedError` and marked with the sliding-window algorithm to implement next.
- (Chris / Task 3 -- receiver) `receiver.py` is fully implemented and merged (PR #1). The Go-Back-N receiver accepts in-order DATA packets, drops duplicates/out-of-order/corrupted packets, and replies with cumulative ACKs (`ack_num = expected_seq`). Handles FIN cleanly. `tests/test_receiver.py` has 5 passing unit tests covering in-order delivery, duplicate drop, out-of-order drop, corruption drop, and FIN detection.
- (Neha / Task 4 -- testbed/eval) `congestion.py` class skeleton is in place with `cwnd`, `ssthresh`, and state fields initialized; `on_ack()`, `on_timeout()`, and `on_triple_dup_ack()` are stubbed. `eval/setup_netem.sh` is complete and ready -- it applies `tc netem` loss and delay to a network interface. `eval/run_experiments.py` has the loss/delay sweep parameters and function outlines.

## Challenges encountered
- Settling on the ACK convention required explicit coordination between the sender (Task 2) and receiver (Task 3): we landed on a cumulative scheme where `ack_num` means "next seq I expect," matching TCP semantics, so the sender slides its window base directly to `ack_num`.
- The `netem` testbed only works on Linux, so the evaluation will need to run in the Docker lab environment rather than on Windows dev machines.

## Adjustments to the plan
- Switched the implementation language from C to Python.
- Adopted Go-Back-N for Phase 1 of the receiver (simpler to get right), with a Selective Repeat upgrade path already sketched at the bottom of `receiver.py` for Phase 2.

## Evidence of progress
- GitHub commit history: https://github.com/nhulchris/anti-hackers-rdt/commits/main
- Project board screenshot (Todo / In Progress / In Review / Done) -- *to be inserted*
- Screenshot of a successful transfer (and one under injected packet loss) -- *pending sender implementation*

## Plan before Progress Report 2
- (Theo) Implement `Sender.send()`: stop-and-wait first (one packet in flight, wait for ACK, retransmit on timeout), then expand to the full sliding window. Add `test_sender.py`.
- (Neha) Implement `CongestionControl.on_ack()` and `on_timeout()` (slow start + AIMD). Complete `run_experiments.py` to sweep loss rates and produce throughput/goodput metrics. Run at least one baseline experiment in the Docker lab.
- (Chris) Phase 2 receiver upgrade: add out-of-order buffering (Selective Repeat), update `advertised_window` to reflect real free buffer space, and coordinate with Theo on the retransmit-only-lost-packet behavior.
- (All) End-to-end integration test: sender + receiver transferring a real file, confirmed correct on the other side.
