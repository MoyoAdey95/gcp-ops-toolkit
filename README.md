# gcp-ops-toolkit

Small command-line utilities for inspecting the health and configuration of a
GCP environment. Some version of these checks is what I actually run before
and after a deploy. This is that, packaged up as something inspectable rather
than left as one-off gcloud commands in my shell history. Personal lab
project, not client or production code.

Built with AI-assisted tooling, designed, tested and operated by me against my
own GCP lab environment (see companion repo `gcp-terraform-lab`).

## Safety model

Every tool here is read-only. That wasn't a hard call. This is discovery
tooling, and discovery tooling that can also change things is a foot-gun
waiting to happen. If I ever want it to fix what it finds, that belongs in
reviewed Terraform, not a script I run half-awake before a deploy.

Missing permissions or a disabled API get you a plain error message and a
non-zero exit code, not a Python traceback. And output works both ways.
`--format table` by default because that's what I actually read, `--format
json` when I want to pipe it into something else.

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
That's deliberate. It needs no key handling, works with whatever auth you already
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

Formatting and threshold logic is unit-tested. Anything needing live GCP is
exercised by running the tools against the lab environment.

## Why each tool exists

`cloudrun_health` and `deploy_verify` both come down to the same question
after a deploy. Is the revision actually ready and is traffic pointed at it?
That's answerable from two fields in the service description, so I'd rather
run a command than click through the console to find them.

`iam_audit` exists because primitive roles creep in quietly. First real run
against this project flagged the default compute service account sitting on
`roles/editor` (it's in `examples/`), which I hadn't gone looking for and
wouldn't have noticed otherwise.

`pubsub_backlog` exists because a stalled consumer shows up as a growing
backlog before anyone downstream notices anything's wrong. I'd rather see
that in a terminal than find out from a Slack message.

`api_preflight` exists because "API not enabled" failing you halfway through
a deploy is completely avoidable. Check first.
