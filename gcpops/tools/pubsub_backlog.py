"""Pub/Sub subscription backlog check.

A growing backlog is usually the first visible symptom of dead or stalled
consumers: it shows up before users complain. Backlog depth only exists as a
Cloud Monitoring metric (num_undelivered_messages), so this tool uses the
Monitoring client library rather than gcloud.
"""

import sys
import time

from gcpops.common.cli import base_parser
from gcpops.common.output import print_result


def classify(value: int, warn: int, crit: int) -> str:
    """Threshold logic, kept pure so it's unit-testable."""
    if value >= crit:
        return "CRIT"
    if value >= warn:
        return "WARN"
    return "ok"


def collect(project: str, warn: int, crit: int, window_secs: int = 600) -> list[dict]:
    # imported here so the rest of the toolkit works without this dependency
    from google.cloud import monitoring_v3

    client = monitoring_v3.MetricServiceClient()
    now = time.time()
    interval = monitoring_v3.TimeInterval(
        {
            "end_time": {"seconds": int(now)},
            "start_time": {"seconds": int(now - window_secs)},
        }
    )

    results = client.list_time_series(
        request={
            "name": f"projects/{project}",
            "filter": (
                'metric.type = "pubsub.googleapis.com/subscription/'
                'num_undelivered_messages"'
            ),
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
        }
    )

    rows = []
    for series in results:
        sub = series.resource.labels.get("subscription_id", "?")
        points = list(series.points)
        latest = int(points[0].value.int64_value) if points else 0
        rows.append(
            {
                "subscription": sub,
                "undelivered": latest,
                "status": classify(latest, warn, crit),
            }
        )
    return sorted(rows, key=lambda r: -r["undelivered"])


def main() -> int:
    parser = base_parser(__doc__)
    parser.add_argument("--warn", type=int, default=100, help="warning threshold")
    parser.add_argument("--crit", type=int, default=1000, help="critical threshold")
    args = parser.parse_args()

    try:
        rows = collect(args.project, args.warn, args.crit)
    except Exception as exc:  # surface auth/API errors cleanly
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print_result(rows, ["subscription", "undelivered", "status"], args.format)

    if any(r["status"] == "CRIT" for r in rows):
        return 2
    if any(r["status"] == "WARN" for r in rows):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
