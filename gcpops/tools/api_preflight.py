"""Pre-deployment API check: are the services a deployment needs enabled?

"API has not been used in project..." halfway through a deploy is an
avoidable failure mode. Check prerequisites before touching anything.
"""

import sys

from gcpops.common import gcloud
from gcpops.common.cli import base_parser
from gcpops.common.output import print_result

# sensible default for the companion gcp-terraform-lab stack
DEFAULT_REQUIRED = [
    "run",
    "compute",
    "artifactregistry",
    "secretmanager",
    "monitoring",
    "iam",
]


def collect(project: str, required: list[str]) -> list[dict]:
    enabled = gcloud.run(["services", "list", "--enabled"], project=project) or []
    enabled_names = {
        s.get("config", {}).get("name", s.get("name", "")) for s in enabled
    }

    rows = []
    for short in required:
        full = short if "." in short else f"{short}.googleapis.com"
        ok = any(full in name for name in enabled_names)
        rows.append({"api": full, "enabled": "yes" if ok else "NO"})
    return rows


def main() -> int:
    parser = base_parser(__doc__)
    parser.add_argument(
        "--required",
        default=",".join(DEFAULT_REQUIRED),
        help="comma-separated API names (short or full)",
    )
    args = parser.parse_args()

    required = [r.strip() for r in args.required.split(",") if r.strip()]

    try:
        rows = collect(args.project, required)
    except gcloud.GcloudError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print_result(rows, ["api", "enabled"], args.format)

    missing = [r for r in rows if r["enabled"] == "NO"]
    if missing:
        print(f"\nFAIL: {len(missing)} required API(s) not enabled", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
