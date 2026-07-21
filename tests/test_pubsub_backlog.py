"""Unit tests for backlog threshold classification (no GCP required)."""

from gcpops.tools.pubsub_backlog import classify


def test_classify_thresholds():
    assert classify(0, warn=100, crit=1000) == "ok"
    assert classify(99, warn=100, crit=1000) == "ok"
    assert classify(100, warn=100, crit=1000) == "WARN"
    assert classify(999, warn=100, crit=1000) == "WARN"
    assert classify(1000, warn=100, crit=1000) == "CRIT"
