"""Post-deployment smoke check for a Cloud Run service.

Confirms the service reports Ready, 100% of traffic is on the latest ready
revision (or intentionally split), and, if --url is given, that the health
endpoint actually answers. The difference between "deploy command exited 0"
and "the thing is serving".
"""

import sys
import urllib.error
import urllib.request

from gcpops.common import gcloud
from gcpops.common.cli import base_parser
from gcpops.common.output import print_json


def check_service(project: str, region: str, service: str) -> dict:
    svc = gcloud.run(
        ["run", "services", "describe", service, f"--region={region}"],
        project=project,
    ) or {}

    status = svc.get("status", {})
    conditions = {c.get("type"): c for c in status.get("conditions", [])}
    ready = conditions.get("Ready", {}).get("status", "Unknown")

    latest = status.get("latestReadyRevisionName", "")
    traffic = status.get("traffic") or []
    on_latest = sum(
        t.get("percent", 0)
        for t in traffic
        if t.get("revisionName") == latest or t.get("latestRevision")
    )

    return {
        "service": service,
        "ready": ready,
        "latest_ready_revision": latest,
        "traffic_on_latest_pct": on_latest,
        "url": status.get("url", ""),
    }


def check_endpoint(url: str, path: str = "/health", timeout: int = 10) -> dict:
    target = url.rstrip("/") + path
    try:
        with urllib.request.urlopen(target, timeout=timeout) as resp:
            return {"endpoint": target, "http_status": resp.status}
    except urllib.error.HTTPError as exc:
        return {"endpoint": target, "http_status": exc.code}
    except Exception as exc:
        return {"endpoint": target, "http_status": None, "error": str(exc)}


def main() -> int:
    parser = base_parser(__doc__)
    parser.add_argument("--region", required=True)
    parser.add_argument("--service", required=True)
    parser.add_argument("--url", default="", help="base URL to smoke-test (optional)")
    args = parser.parse_args()

    try:
        result = check_service(args.project, args.region, args.service)
    except gcloud.GcloudError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.url:
        result["smoke"] = check_endpoint(args.url)

    print_json(result)

    ok = (
        result["ready"] == "True"
        and result["traffic_on_latest_pct"] == 100
        and (not args.url or result["smoke"].get("http_status") == 200)
    )
    if not ok:
        print("\nFAIL: deployment verification failed", file=sys.stderr)
        return 1
    print("\nOK: deployment verified", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
