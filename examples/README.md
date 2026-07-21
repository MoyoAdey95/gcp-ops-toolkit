# Example output

Real output from running these tools against my own GCP lab project
(`moyo-cloud-lab`, the same project `gcp-terraform-lab` deploys into).
Captured mid-July 2026, mostly during a single evening of running each
tool for the first time after writing it.

## cloudrun_health

```
service     ready  latest_ready          traffic                    url
----------  -----  --------------------  -------------------------  ------------------------------------------
tf-lab-api  True   tf-lab-api-00001-s22  tf-lab-api-00001-s22=100%  https://tf-lab-api-awypnoptaa-ew.a.run.app
```

## iam_audit

```
member                                                                               role                                            flag
-----------------------------------------------------------------------------------  ----------------------------------------------  ---------
serviceAccount:401347140946-compute@developer.gserviceaccount.com                    roles/editor                                    PRIMITIVE
user:moyoadey95@gmail.com                                                            roles/owner                                     PRIMITIVE
serviceAccount:401347140946@cloudservices.gserviceaccount.com                        roles/compute.instanceGroupManagerServiceAgent
serviceAccount:service-401347140946@compute-system.iam.gserviceaccount.com           roles/compute.serviceAgent
serviceAccount:service-401347140946@containerregistry.iam.gserviceaccount.com        roles/containerregistry.ServiceAgent
serviceAccount:service-401347140946@gcp-sa-artifactregistry.iam.gserviceaccount.com  roles/artifactregistry.serviceAgent
serviceAccount:service-401347140946@gcp-sa-pubsub.iam.gserviceaccount.com            roles/pubsub.serviceAgent
serviceAccount:service-401347140946@serverless-robot-prod.iam.gserviceaccount.com    roles/run.serviceAgent
WARNING: 2 primitive-role binding(s) found. Consider replacing with predefined roles.
```

The interesting row here isn't my own owner binding, it's the first one:
`401347140946-compute@developer.gserviceaccount.com` on `roles/editor`.
That's the default compute service account, and GCP grants it editor on
every project automatically. I hadn't gone looking for that, the tool
found it on its first run. The production fix is an org policy that
disables automatic role grants on default service accounts.

## api_preflight

Default check, the set of APIs `gcp-terraform-lab` actually depends on:

```
api                               enabled
-------------------------------  -------
run.googleapis.com               yes
compute.googleapis.com           yes
artifactregistry.googleapis.com  yes
secretmanager.googleapis.com     yes
monitoring.googleapis.com        yes
iam.googleapis.com               yes
```

Fail path, checking for an API that's genuinely never been enabled on this
project (GKE):

```
api                           enabled
----------------------------  -------
run.googleapis.com            yes
secretmanager.googleapis.com  yes
container.googleapis.com      NO
FAIL: 1 required API(s) not enabled
```

One thing worth flagging. An earlier version of this check used `bigquery`
as the "missing" example, and it came back `yes`. Turned out BigQuery is
one of a handful of APIs Google auto-enables on every new project,
regardless of whether you ever touch it. Not a bug in the tool, just a
reminder that "never used" and "not enabled" aren't the same thing.

## deploy_verify

```
{
  "service": "tf-lab-api",
  "ready": "True",
  "latest_ready_revision": "tf-lab-api-00001-s22",
  "traffic_on_latest_pct": 100,
  "url": "https://tf-lab-api-awypnoptaa-ew.a.run.app",
  "smoke": {
    "endpoint": "https://tf-lab-api-awypnoptaa-ew.a.run.app/health",
    "http_status": 200
  }
}
OK: deployment verified
```

## pubsub_backlog

Created a throwaway topic and subscription, published 5 messages with
nothing consuming them, then ran the tool:

```
subscription          undelivered  status
--------------------  -----------  ------
ops-toolkit-demo-sub  5            ok
```

Two things I hadn't anticipated going in. First, the metric took close to
five minutes to show up after the first publish. Cloud Monitoring's first
data point for a brand-new subscription isn't instant, so `(no results)`
right after publishing doesn't mean the tool is broken. Second, after I
deleted the subscription, a rerun of `ops_report` still showed it with the
same backlog of 5 for several more minutes. That's because this tool
queries a 10-minute rolling window of historical metric data, not a live
list of subscriptions. A deleted resource's last data point stays inside
that window until it ages out, worth knowing before assuming a stale
result means the tool queried the wrong thing.

## ops_report

Composed run, same evening, primitive roles still present and the
throwaway Pub/Sub subscription still live:

```
== Cloud Run services ==
service     ready  latest_ready          traffic
----------  -----  --------------------  -------------------------
tf-lab-api  True   tf-lab-api-00001-s22  tf-lab-api-00001-s22=100%
== IAM: primitive roles ==
member                                                             role
-----------------------------------------------------------------  ------------
serviceAccount:401347140946-compute@developer.gserviceaccount.com  roles/editor
user:moyoadey95@gmail.com                                          roles/owner
== Required APIs ==
all enabled
== Pub/Sub backlog ==
subscription          undelivered  status
--------------------  -----------  ------
ops-toolkit-demo-sub  5            ok
ISSUES FOUND: 2
```

Exit code 1, correctly. Two primitive-role bindings are real issues on this
project, even though one of them is expected (my own owner access on a lab
I run solo). That's the tradeoff of a blunt check, it flags things you
already know about alongside things you don't, and you still have to read
the output.

## A note on Python version

Developed and tested against Python 3.9 (this machine's default via
Anaconda). `google-cloud-monitoring` and its dependencies print
`FutureWarning`s about 3.9 being past end of life. They're stripped from
the output above for readability. They don't affect functionality. Worth
upgrading the venv to 3.10+ at some point, but hasn't been necessary yet.
