"""Unit tests for the TCP-style congestion controller."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from congestion import CongestionControl  # noqa: E402


def test_starts_with_one_packet_window():
    cc = CongestionControl()

    assert cc.cwnd == 1.0
    assert cc.window == 1
    assert cc.state == "slow_start"


def test_slow_start_switches_at_threshold():
    cc = CongestionControl()
    cc.ssthresh = 4.0

    cc.on_ack()
    cc.on_ack()
    cc.on_ack()

    assert cc.cwnd == 4.0
    assert cc.state == "congestion_avoidance"


def test_congestion_avoidance_uses_additive_increase():
    cc = CongestionControl()
    cc.cwnd = 4.0
    cc.state = "congestion_avoidance"

    cc.on_ack()

    assert cc.cwnd == pytest.approx(4.25)
    assert cc.window == 4


def test_timeout_halves_threshold_and_restarts_slow_start():
    cc = CongestionControl()
    cc.cwnd = 12.0
    cc.state = "congestion_avoidance"

    cc.on_timeout()

    assert cc.ssthresh == 6.0
    assert cc.cwnd == 1.0
    assert cc.window == 1
    assert cc.state == "slow_start"


def test_triple_duplicate_ack_uses_fast_recovery_window():
    cc = CongestionControl()
    cc.cwnd = 10.0

    cc.on_triple_dup_ack()

    assert cc.ssthresh == 5.0
    assert cc.cwnd == 5.0
    assert cc.state == "congestion_avoidance"
