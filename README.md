# gcp-ops-toolkit

Small command-line utilities for inspecting the health and configuration of a
GCP environment. These are the kind of checks I run (in some form) before and
after deployments in real operations work, packaged here as a standalone,
inspectable toolkit. Personal lab project, not client or production code.

Built with AI-assisted tooling; designed, tested and operated by me against my
own GCP lab environment (see companion repo `gcp-terraform-lab`).

## Safety model

This reflects how I actually work on production systems: discovery before
change, low-risk investigation before anything that could have impact.

- **Every tool is read-only.** Nothing here mutates infrastructure.
- **Failures are explicit.** Missing permissions or disabled APIs produce a
  clear message and a non-zero exit code, not a stack trace.
- **Output is for humans and machines.** `--format table` (default) for eyes,
  `--format json` for piping into other tooling.

## Tools

| Tool | What it answers |
|------|-----------------|
| `cloudrun_health` | Are my Cloud Run services ready, and where is traffic going? |
| `iam_audit` | Who has which roles, and are any primitive roles (owner/editor/viewer) in use? |
| `pubsub_backlog` | Are subscriptions keeping up, or is a backlog building? |
| `api_preflight` | Are the APIs a deployment needs actually enabled? |
| `deploy_verify` | Did the deployment I just did actually succeed and serve? |
| `ops_report` | One-shot summary of all of the above. |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

gcloud auth login
gcloud auth application-default login   # needed by pubsub_backlog (Monitoring API)
```

Requires the gcloud CLI. Most tools shell out to `gcloud --format=json`.
That's deliberate: it needs no key handling, works with whatever auth you already
have, and mirrors how an engineer actually investigates. `pubsub_backlog` uses
the Cloud Monitoring client library instead, because backlog depth only exists
as a monitoring metric.

## Usage

```bash
python -m gcpops.tools.cloudrun_health --project my-project --region europe-west1
python -m gcpops.tools.iam_audit --project my-project
python -m gcpops.tools.pubsub_backlog --project my-project --warn 100 --crit 1000
python -m gcpops.tools.api_preflight --project my-project --required run,secretmanager
python -m gcpops.tools.deploy_verify --project my-project --region europe-west1 \
    --service tf-lab-api --url https://tf-lab-api-xxxx.run.app
python -m gcpops.tools.ops_report --project my-project --region europe-west1
```

Every tool supports `--format json` and exits non-zero on warnings/failures,
so they can gate CI steps.

## Example output

See `examples/`, captured from real runs against my lab environment.

## Tests

```bash
python -m pytest tests/
```

Formatting and threshold logic is unit-tested; anything needing live GCP is
exercised by running the tools against the lab environment.

## Why each tool exists (the operational story)

- **cloudrun_health / deploy_verify:** most "is it down?" questions after a
  deploy are answered by revision readiness and traffic split. Checking beats
  guessing.
- **iam_audit:** primitive roles accumulate quietly and are invisible until
  audited. This makes the audit a 5-second habit.
- **pubsub_backlog:** a growing backlog is the earliest symptom of dead
  workers; it pages you before users notice.
- **api_preflight:** "API not enabled" mid-deploy is an avoidable failure;
  check prerequisites before touching anything.
