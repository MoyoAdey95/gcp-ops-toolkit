"""Cloud Run service health: readiness, traffic split, latest revision.

Answers the post-deploy question "is everything actually serving?" without
clicking through the console.
"""

import sys

from gcpops.common import gcloud
from gcpops.common.cli import base_parser
from gcpops.common.output import print_result


def collect(project: str, region: str) -> list[dict]:
    services = gcloud.run(
        ["run", "services", "list", f"--region={region}"], project=project
    ) or []

    rows = []
    for svc in services:
        status = svc.get("status", {})
        conditions = {c.get("type"): c for c in status.get("conditions", [])}
        ready = conditions.get("Ready", {}).get("status", "Unknown")

        traffic = status.get("traffic") or []
        split = ", ".join(
            f"{t.get('revisionName', 'latest')}={t.get('percent', 0)}%"
            for t in traffic
            if t.get("percent")
        )

        rows.append(
            {
                "service": svc.get("metadata", {}).get("name", "?"),
                "ready": ready,
                "latest_ready": status.get("latestReadyRevisionName", "-"),
                "traffic": split or "-",
                "url": status.get("url", "-"),
            }
        )
    return rows


def main() -> int:
    parser = base_parser(__doc__)
    parser.add_argument("--region", required=True, help="Cloud Run region")
    args = parser.parse_args()

    try:
        rows = collect(args.project, args.region)
    except gcloud.GcloudError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print_result(rows, ["service", "ready", "latest_ready", "traffic", "url"], args.format)

    unhealthy = [r for r in rows if r["ready"] != "True"]
    if unhealthy:
        print(f"\nWARNING: {len(unhealthy)} service(s) not ready", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
