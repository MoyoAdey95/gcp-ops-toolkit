"""Project IAM audit: full binding list, with primitive roles flagged.

Primitive roles (owner/editor/viewer) accumulate quietly, especially editor
on default service accounts, and stay invisible until someone looks. This
makes looking cheap.
"""

import sys

from gcpops.common import gcloud
from gcpops.common.cli import base_parser
from gcpops.common.output import print_result

PRIMITIVE_ROLES = {"roles/owner", "roles/editor", "roles/viewer"}


def collect(project: str) -> list[dict]:
    policy = gcloud.run(["projects", "get-iam-policy", project]) or {}

    rows = []
    for binding in policy.get("bindings", []):
        role = binding.get("role", "?")
        for member in binding.get("members", []):
            rows.append(
                {
                    "member": member,
                    "role": role,
                    "flag": "PRIMITIVE" if role in PRIMITIVE_ROLES else "",
                }
            )
    return sorted(rows, key=lambda r: (r["flag"] == "", r["member"]))


def main() -> int:
    parser = base_parser(__doc__)
    args = parser.parse_args()

    try:
        rows = collect(args.project)
    except gcloud.GcloudError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print_result(rows, ["member", "role", "flag"], args.format)

    flagged = [r for r in rows if r["flag"]]
    if flagged:
        print(
            f"\nWARNING: {len(flagged)} primitive-role binding(s) found. "
            "Consider replacing with predefined roles.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
