"""Unit tests for output formatting (no GCP required)."""

from gcpops.common.output import format_table


def test_format_table_empty():
    assert format_table([], ["a"]) == "(no results)"


def test_format_table_alignment():
    rows = [{"name": "svc-a", "ready": "True"}, {"name": "a-longer-name", "ready": "False"}]
    out = format_table(rows, ["name", "ready"])
    lines = out.splitlines()
    assert len(lines) == 4  # header, rule, 2 rows
    assert lines[0].startswith("name")
    assert "a-longer-name" in lines[3]
    # all lines padded to consistent column starts
    assert lines[2].index("True") == lines[3].index("False")


def test_format_table_missing_keys():
    rows = [{"name": "x"}]
    out = format_table(rows, ["name", "ready"])
    assert "x" in out  # missing key renders empty, no crash
