"""Output helpers: aligned tables for humans, JSON for machines."""

import json


def print_json(data) -> None:
    print(json.dumps(data, indent=2, default=str))


def format_table(rows: list[dict], columns: list[str]) -> str:
    """Render dict rows as an aligned text table. Pure function (tested)."""
    if not rows:
        return "(no results)"

    widths = {c: len(c) for c in columns}
    for row in rows:
        for c in columns:
            widths[c] = max(widths[c], len(str(row.get(c, ""))))

    header = "  ".join(c.ljust(widths[c]) for c in columns)
    rule = "  ".join("-" * widths[c] for c in columns)
    lines = [header, rule]
    for row in rows:
        lines.append("  ".join(str(row.get(c, "")).ljust(widths[c]) for c in columns))
    return "\n".join(lines)


def print_result(rows: list[dict], columns: list[str], fmt: str) -> None:
    if fmt == "json":
        print_json(rows)
    else:
        print(format_table(rows, columns))
