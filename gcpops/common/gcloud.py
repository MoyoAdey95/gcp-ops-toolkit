"""Thin wrapper around the gcloud CLI.

The tools shell out to gcloud rather than using individual client libraries:
no key handling, works with existing auth, and mirrors how an engineer
investigates interactively. The trade-off (slower, needs gcloud installed) is
acceptable for operational tooling.
"""

import json
import shutil
import subprocess


class GcloudError(RuntimeError):
    """A gcloud invocation failed in a way the caller should surface."""


def run(args: list[str], project: str | None = None) -> list | dict:
    """Run a gcloud command with --format=json and return parsed output."""
    if shutil.which("gcloud") is None:
        raise GcloudError("gcloud CLI not found on PATH")

    cmd = ["gcloud", *args, "--format=json"]
    if project:
        cmd.append(f"--project={project}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "PERMISSION_DENIED" in stderr or "does not have permission" in stderr:
            raise GcloudError(
                f"permission denied running: {' '.join(cmd)}\n"
                f"hint: check your account's roles on project {project!r}"
            )
        if "is not enabled" in stderr or "has not been used" in stderr:
            raise GcloudError(
                f"required API not enabled for: {' '.join(cmd)}\n{stderr}"
            )
        raise GcloudError(f"gcloud failed ({result.returncode}): {stderr}")

    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        raise GcloudError(f"could not parse gcloud output as JSON: {exc}") from exc
