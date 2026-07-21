"""One-shot environment health report: composes the other tools.

The morning-coffee command: one run answers "is anything obviously wrong?"
"""

import sys

from gcpops.common import gcloud
from gcpops.common.cli import base_parser
from gcpops.common.output import format_table
from gcpops.tools import api_preflight, cloudrun_health, iam_audit


def main() -> int:
    parser = base_parser(__doc__)
    parser.add_argument("--region", required=True)
    parser.add_argument(
        "--skip-pubsub",
        action="store_true",
        help="skip the backlog check (needs Monitoring API + ADC)",
    )
    args = parser.parse_args()

    issues = 0

    print("== Cloud Run services ==")
    try:
        rows = cloudrun_health.collect(args.project, args.region)
        print(format_table(rows, ["service", "ready", "latest_ready", "traffic"]))
        issues += sum(1 for r in rows if r["ready"] != "True")
    except gcloud.GcloudError as exc:
        print(f"error: {exc}", file=sys.stderr)
        issues += 1

    print("\n== IAM: primitive roles ==")
    try:
        rows = [r for r in iam_audit.collect(args.project) if r["flag"]]
        print(format_table(rows, ["member", "role"]) if rows else "none found")
        issues += len(rows)
    except gcloud.GcloudError as exc:
        print(f"error: {exc}", file=sys.stderr)
        issues += 1

    print("\n== Required APIs ==")
    try:
        rows = api_preflight.collect(args.project, api_preflight.DEFAULT_REQUIRED)
        missing = [r for r in rows if r["enabled"] == "NO"]
        print(format_table(missing, ["api", "enabled"]) if missing else "all enabled")
        issues += len(missing)
    except gcloud.GcloudError as exc:
        print(f"error: {exc}", file=sys.stderr)
        issues += 1

    if not args.skip_pubsub:
        print("\n== Pub/Sub backlog ==")
        try:
            from gcpops.tools import pubsub_backlog

            rows = pubsub_backlog.collect(args.project, warn=100, crit=1000)
            print(
                format_table(rows, ["subscription", "undelivered", "status"])
                if rows
                else "no subscriptions with metrics"
            )
            issues += sum(1 for r in rows if r["status"] != "ok")
        except Exception as exc:
            print(f"error: {exc}", file=sys.stderr)
            issues += 1

    print(f"\n{'ISSUES FOUND: ' + str(issues) if issues else 'ALL CLEAR'}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
