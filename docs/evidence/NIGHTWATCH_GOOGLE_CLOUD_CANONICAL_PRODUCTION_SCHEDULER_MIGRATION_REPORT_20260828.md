# NIGHTWATCH Google Cloud Canonical Production Scheduler Migration

Date: 2026-08-28

```text
CURRENT_MAIN_SHA=6883971466e7c6cea0282be122cf14318ce4aaba
GCP_MIGRATION_RESULT=PASS_DEPLOYED_AWAITING_NATURAL_RUN
GCP_DEPLOYMENT_STATUS=ACTIVE_PRIVATE_AUTHENTICATED_AWAITING_NATURAL_2026_08_28_DEALER_AND_ACTIVITY

ROOT_CAUSE_ACCEPTED=DELAYED_GITHUB_SCHEDULED_EVENT_DELIVERY
TIMEZONE_MISCONFIGURATION_FOUND=NO
GITHUB_SCHEDULE_EVENT_DELAY_CONFIRMED=YES

SLOT_MODEL=IMMUTABLE_CANONICAL_SLOT_PLUS_APPEND_ONLY_DELIVERY_ATTEMPTS
CANONICAL_SLOT_UNIQUENESS=UNIQUE_SLOT_TYPE_AND_INTENDED_AT_PLUS_UNIQUE_CANONICAL_KEY
INTENDED_TIME_SOURCE=X_CLOUDSCHEDULER_SCHEDULETIME_RFC3339
ACTUAL_TIME_SOURCE=UTC_NOW_AT_AUTHENTICATED_HTTP_HANDLER_ENTRY
CROSS_MIDNIGHT_CORRECTION=INTENDED_MARKET_DATE_DRIVES_ACTIVITY_SESSION_AND_SCAN_MARKET_IDENTITY
RADAR_ACTUAL_WINDOW_GUARD_PRESERVED=YES_0600_TO_0800_AMERICA_NEW_YORK_AND_ACTUAL_DATE_MUST_MATCH_INTENDED_DATE

GCP_CLOUD_RUN_SERVICE=nightwatch-production-orchestrator
GCP_SCHEDULER_JOB_RADAR_OI=nightwatch-radar-oi
GCP_SCHEDULER_JOB_DEALER_GEX=nightwatch-dealer-gex
GCP_SCHEDULER_JOB_ACTIVITY_VNEXT=nightwatch-activity-vnext
GCP_TIMEZONE=America/New_York
GCP_AUTH_MODEL=INTERNAL_ONLY_CLOUD_RUN_PLUS_OIDC_PLUS_DEDICATED_RUN_INVOKER_SERVICE_ACCOUNT
GCP_SECRET_MODEL=SECRET_MANAGER_RUNTIME_REFERENCES_WITH_SECRET_LEVEL_ACCESSOR_GRANTS
GCP_PROJECT_ID=nightwatch-production
GCP_REGION=asia-northeast1
GCP_CONTAINER_IMAGE=asia-northeast1-docker.pkg.dev/nightwatch-production/nightwatch-production/nightwatch-production-orchestrator@sha256:8ab059afdd6b4d165faebd1f699367b06f01f8c5b3f14da74db8e19490ae89ab
GCP_CLOUD_RUN_REVISION=nightwatch-production-orchestrator-00002-jss
GCP_AUTHENTICATED_HEALTH=PASS_HTTP_200_POST_HEALTH_VIA_SAME_PROJECT_SCHEDULER_OIDC
GCP_SCHEDULER_JOBS_CREATED=YES_ALL_THREE
GCP_SCHEDULER_JOBS_PAUSED=NO_ALL_THREE_ENABLED
GCP_TEMP_HEALTH_JOB=nightwatch-health-validation-temp-20260828_CREATED_INVOKED_ONCE_DELETED
CUTOVER_DEFAULT_BRANCH_SHA=6883971466e7c6cea0282be122cf14318ce4aaba
GCP_PRODUCTION_TRANSPORT_ACTIVATION_DATE=2026-08-28
FIRST_FULL_THREE_SLOT_GCP_CANONICAL_MARKET_DATE=2026-08-31_EXPECTED_NEXT_ELIGIBLE_XNYS_SESSION
GCP_RADAR_OI_JOB_ENABLED=YES
GCP_DEALER_GEX_JOB_ENABLED=YES
GCP_ACTIVITY_VNEXT_JOB_ENABLED=YES
GCP_RADAR_OI_NEXT_INTENDED_MARKET_DATE=2026-08-31
GCP_DEALER_GEX_NEXT_INTENDED_MARKET_DATE=2026-08-28
GCP_ACTIVITY_VNEXT_NEXT_INTENDED_MARKET_DATE=2026-08-28

GITHUB_AUTOMATIC_RADAR_ACTIVE=NO
GITHUB_AUTOMATIC_ACTIVITY_ACTIVE=NO
GITHUB_AUTOMATIC_DEALER_GEX_ACTIVE=NO
GITHUB_MANUAL_DISPATCH_PRESERVED=YES

MANUAL_CANONICAL_LEAKAGE_FOUND=YES
MANUAL_CANONICAL_LEAKAGE_REMEDIATED=YES

STAGE9_TRIGGER_COMPATIBILITY=PRESERVED
EXPECTED_PRODUCTION_SCAN_TRIGGER=scheduled_daily

TESTS=PASS_BACKEND_472_FRONTEND_13_PLUS_GLOSSARY_LINT_BUILD
ALEMBIC_HEAD=20260828_0020_SINGLE_HEAD
ALEMBIC_CURRENT=20260828_0020_REMOTE_APPLIED
SECRET_SCAN=PASS_VALUE_SAFE_BOUNDARY_AND_HIGH_CONFIDENCE_SIGNATURE_SCANS
WORKTREE_STATUS=CLEAN_AFTER_ACTIVATION_EVIDENCE_COMMIT

NIGHTWATCH_REQUESTS_THIS_TASK=0
PAID_UNITS_THIS_TASK=0
NIGHTWATCH_REQUESTS_CAUSED_BY_ACTIVATION=0
PAID_UNITS_CAUSED_BY_ACTIVATION=0
NIGHTWATCH_REQUESTS_DURING_CUTOVER=0
PAID_UNITS_DURING_CUTOVER=0
GCP_2026_08_28_RADAR_BACKFILL_PERFORMED=NO
GCP_2026_08_28_CANONICAL_SLOT_CREATED=NO_AT_ACTIVATION
REMOTE_DB_WRITES_THIS_TASK=1_TRANSACTIONAL_SCHEMA_MIGRATION_20260828_0020
GCP_RESOURCES_CREATED=18_PERSISTENT_TERRAFORM_RESOURCES_PLUS_1_AUTHORIZED_TEMP_HEALTH_JOB_DELETED
GCP_ESTIMATED_FIXED_MONTHLY_COST=USD_0_IF_CURRENT_FREE_TIER_AVAILABLE_UP_TO_USD_0_42_IF_SCHEDULER_AND_TWO_SECRET_VERSIONS_FULLY_BILLABLE

FIRST_NATURAL_GCP_PRODUCTION_RUN_VERIFIED=NO
FIRST_GCP_CANONICAL_CANDIDATE_OBSERVED=NO

DEALER_GEX_INTENDED_AT=PENDING_NATURAL_2026_08_28_1530_AMERICA_NEW_YORK
DEALER_GEX_ACTUAL_STARTED_AT=PENDING_NATURAL_RUN
DEALER_GEX_EXECUTION_DELAY=PENDING_NATURAL_RUN
DEALER_GEX_TERMINAL_STATUS=PENDING_NATURAL_RUN
DEALER_GEX_CANONICAL_SLOT_COUNT=0_AT_ACTIVATION
DEALER_GEX_NETWORK_ATTEMPTS=0_AT_ACTIVATION
DEALER_GEX_PAID_UNITS=0_AT_ACTIVATION

ACTIVITY_INTENDED_AT=PENDING_NATURAL_2026_08_28_1630_AMERICA_NEW_YORK
ACTIVITY_ACTUAL_STARTED_AT=PENDING_NATURAL_RUN
ACTIVITY_EXECUTION_DELAY=PENDING_NATURAL_RUN
ACTIVITY_TERMINAL_STATUS=PENDING_NATURAL_RUN
ACTIVITY_CANONICAL_SLOT_COUNT=0_AT_ACTIVATION
ACTIVITY_MAG7_COVERAGE=PENDING_NATURAL_RUN
VNEXT_READINESS_STATUS=PENDING_NATURAL_RUN_EXPECTED_FAIL_CLOSED_WITHOUT_CANONICAL_RADAR
VNEXT_SCAN_EXECUTED=NO_AT_ACTIVATION
VNEXT_SCAN_TRIGGER=scheduled_daily_IF_AND_ONLY_IF_CANONICAL_READINESS_PASSES
PRODUCT_CANDIDATE_COUNT=0_AT_ACTIVATION
FIRST_KNOWLEDGE_BASELINE_COUNT=0_AT_ACTIVATION
```

## Gate conclusion

The migration is `PASS_DEPLOYED_AWAITING_NATURAL_RUN`. The billing-enabled project,
deployment identity, database migration, immutable image, private Cloud Run
service, least-privilege IAM, two secret references, and three Scheduler jobs are
deployed and verified. A same-project temporary Scheduler job used the production
OIDC invoker boundary to POST only `/health`; Cloud Run returned HTTP 200 from
revision `nightwatch-production-orchestrator-00002-jss`. The job was invoked exactly
once and immediately deleted. Aggregate before/after evidence shows zero canonical
slots, attempts, candidates, ScanRuns, Daily OI runs, Daily Collection runs, or
Dealer/GEX runs created by health validation.

The workflow-only cutover is active on GitHub default branch `main` at
`6883971466e7c6cea0282be122cf14318ce4aaba`: all automatic production schedules
are absent and both collection workflows retain `workflow_dispatch`. No active or
queued delayed GitHub scheduled execution existed at activation. The three Google
jobs were then resumed without manual execution. At the activation checkpoint the
database still contained zero canonical slots or delivery attempts, and Cloud
Logging showed no canonical endpoint request. The accepted entrypoints remain:

- `python -m app.cli archive-mag7-daily --mode <radar-oi|activity> --scheduled`
- `python -m app.cli run-daily-vnext-observation`
- `Mag7Scanner.execute(trigger="scheduled_daily")`
- `Stage6BalancedContextService.create_baseline(product_candidate_id)`

The Cloud Run wrapper invokes the same service classes directly; it does not
duplicate scanner, scoring, archive, candidate, or baseline logic.

## Implemented design

Alembic revision `20260828_0020` adds:

- one `canonical_scheduler_slots` row per `(slot_type, intended_at)`;
- one append-only `canonical_scheduler_attempts` row per HTTP delivery;
- nullable, unique `canonical_slot_id` ownership on Daily collection, Daily OI,
  Dealer/GEX, and ScanRun rows.

The first delivery commits the slot claim before any Nightwatch client operation.
A duplicate delivery observes the unique owner, records
`DUPLICATE_DELIVERY_REUSED`, and performs no business execution. FAILED,
PARTIAL, MISSED/SKIPPED, and RUNNING owners are not automatically promoted or
retried. A process death after claim therefore fails safe against duplicate spend
and remains visible for explicit remediation.

The authoritative timestamp is Cloud Scheduler's
`X-CloudScheduler-ScheduleTime`. Google documents that this RFC3339 value is the
original schedule time, remains constant across retries, and is suitable for
deduplication. The handler also validates `X-CloudScheduler` and the expected
`X-CloudScheduler-JobName`. The platform authentication boundary remains Cloud
Run IAM/OIDC. See the
[Cloud Scheduler REST header contract](https://docs.cloud.google.com/scheduler/docs/reference/rest/v1/projects.locations.jobs)
and [authenticated Cloud Run scheduling guide](https://docs.cloud.google.com/run/docs/triggering/using-scheduler).

Persisted slot observability includes slot type, intended UTC time, intended New
York market date, actual UTC start, transport, canonical key, terminal status,
paid-attempt flag, network attempts, consumed units, candidate count, baseline
count, and safe child execution IDs/statuses. Execution delay is exactly derivable
from the two persisted timestamps and is returned by the handler. Raw vendor
payloads, Authorization headers, and credentials are not added to scheduler logs.

## Time and source integrity

RADAR_OI keeps the actual 06:00–08:00 ET validity check. It additionally requires
the actual New York date to equal the intended market date. A 06:30 intended slot
delivered at 16:41 is persisted as `SKIPPED_AFTER_SAFE_WINDOW`, constructs no
vendor client, makes zero Nightwatch requests, and cannot be replayed as safe.

ACTIVITY_VNEXT derives its target XNYS session from the intended slot date, not the
actual local calendar date. The actual timestamp must nevertheless be at or after
that intended session's real XNYS close. A prior-day 16:30 slot delivered after
midnight therefore retains the prior session identity, while a future/unclosed
session remains `SKIPPED_BEFORE_SESSION_CLOSE`.

The scanner accepts only a market-date identity override. Its `started_at`,
completion time, candidate materialization time, and
`candidate_first_knowledge_at` continue to use actual `utc_now()`. The Stage 6
baseline cutoff remains the actual candidate first-knowledge timestamp. No
intended time is passed into candidate or baseline timestamp creation.

Dealer/GEX receives the intended market date while preserving the existing
configured 15:30 slot, XNYS calendar, early-close handling, analytical observation
identity, sequential budget, and idempotent surface reuse. No Dealer/GEX analytical
formula or Stage 6 selection rule changed.

## Manual isolation

The diagnostic found a real leakage: Daily Activity, Radar, and Daily OI readiness
queries previously selected date/status rows without checking their parent run
provenance. A human-triggered collection could therefore satisfy scheduled
readiness.

The Google path now requires:

- Activity coverage owned by the current `ACTIVITY_VNEXT` canonical slot;
- Radar and Daily OI coverage owned by a `RADAR_OI` canonical slot for the same
  intended market date.

The former GitHub automatic path required parent run trigger `scheduled`; that
automatic transport is now disabled. `cli` / `workflow_dispatch` evidence cannot
satisfy canonical readiness. GitHub workflow dispatch still collects only and
still contains no vNext scan step.

Dealer/GEX manual-versus-canonical archive selection is separate: Stage 6's
existing point-in-time Dealer/GEX surface selection remains based on immutable
analytical observation identity, vendor time, capture time, and evidence cutoff,
not scheduler transport. A valid manual Dealer/GEX archive can therefore remain
eligible as archived context at or before cutoff. This migration does not change
that Stage 6 policy because Dealer/GEX is not the Activity/Radar/OI production scan
readiness gate; the behavior is recorded for later transport/run-class
decoupling review.

## Security and Google Cloud configuration

Terraform under `infra/gcp` declares six required API enablements, one Artifact
Registry Docker repository, two empty Secret Manager containers, one Cloud Run
service, two dedicated service accounts, two secret-level Secret Manager accessor
grants, one service-level Cloud Run Invoker grant, and three Scheduler jobs. Jobs
default to paused. Terraform never manages secret versions or values. Cloud Run has
internal-only ingress, no `allUsers` binding, zero minimum instances, one maximum
instance, request concurrency one, and a 30-minute timeout. Scheduler uses the
default `run.app` URL, POST, OIDC, the service URL as audience, and
`retry_count=0`.

Google documents that same-project Cloud Scheduler can reach an internal-ingress
Cloud Run service through its default URL while general internet traffic cannot,
and recommends requiring authentication with a dedicated invoker:
[Cloud Run ingress](https://docs.cloud.google.com/run/docs/securing/ingress) and
[Cloud Scheduler HTTP authentication](https://docs.cloud.google.com/scheduler/docs/http-target-auth).

`DATABASE_URL` and `NIGHTWATCH_API_KEY` are injected only from enabled Secret
Manager versions into the server-side runtime. Version existence was verified
without reading either value. Terraform never accepts secret values. The deployed
revision runs the scheduler-only FastAPI app as an unprivileged user and disables
application access logs. Cloud Run request metadata confirmed health status and
revision without logging credentials, headers, or secret values.

## Cutover safety

The previously selected 2026-08-31 activation boundary was explicitly superseded
by Founder authorization on 2026-08-28. Before activation, `origin/main` was
fetched, the workflow-only schedule removal was verified on live GitHub default
branch, active/queued GitHub scheduled-run count was zero, all Google jobs were
paused, exact schedules/URIs/OIDC/retry configuration were rechecked, Cloud Run was
ready and private, Alembic current/head was `20260828_0020`, and the database had
zero canonical slots or attempts.

Activation occurred after 08:00 America/New_York, so the missed 2026-08-28 06:30
RADAR_OI slot was not backfilled, promoted, or manually executed. Its next natural
execution is 2026-08-31 06:30 ET. The remaining natural 2026-08-28 DEALER_GEX and
ACTIVITY_VNEXT slots are scheduled for 15:30 and 16:30 ET. If canonical Radar/OI
evidence is absent, Activity readiness remains fail-closed; no manual or legacy
evidence may substitute for it.

All three resume operations succeeded. Post-activation state is ENABLED with the
expected next execution dates. No canonical job was manually executed. Immediate
post-activation database and Cloud Logging checks remained at zero canonical
slots, attempts, network attempts, and consumed paid units. No period existed in
which both GitHub and Google automatic scheduling were enabled.

## Validation evidence

- Ruff: PASS.
- Full backend pytest: PASS, 472 tests.
- Focused scheduler rerun: PASS, 12 tests.
- Frontend glossary contract: PASS, 34 governed concepts.
- Frontend Stage 7 Node tests: PASS, 13 tests.
- Frontend ESLint: PASS.
- Frontend Next.js production build: PASS.
- Alembic graph: one head, `20260828_0020`.
- Configured remote database current revision: `20260828_0020`, migration applied
  transactionally and verified.
- `git diff --check`: PASS.
- Forbidden frontend Nightwatch / persisted Authorization pattern scan: PASS.
- High-confidence private-key/token signature scan excluding ignored `.env`:
  PASS.
- Native Terraform 1.15.8 init/format/validate: PASS with Google provider 7.46.0.
- Bootstrap Terraform apply: PASS, 11 added, 0 changed, 0 destroyed.
- Full Terraform deployment apply: PASS, 7 added, 0 changed, 0 destroyed; all
  three Scheduler jobs created paused.
- Pre-activation Terraform detailed plan: PASS, no changes with jobs paused.
- Activation-state Terraform synchronization: PASS, 0 added, 0 changed, 0
  destroyed; only the stored `scheduler_jobs_paused=false` output changed.
- Final enabled-state Terraform detailed plan: PASS, no changes.
- Container build: PASS with Docker 29.6.2.
- Local immutable-image `/health`: PASS using non-secret placeholders; no database
  or Nightwatch request.
- Artifact Registry push: PASS at immutable digest
  `sha256:8ab059afdd6b4d165faebd1f699367b06f01f8c5b3f14da74db8e19490ae89ab`.
- Cloud Run: PASS, internal ingress, ready revision
  `nightwatch-production-orchestrator-00002-jss`, no `allUsers` binding.
- Authenticated Cloud Run `/health`: PASS, one same-project Scheduler OIDC POST,
  HTTP 200, expected revision reached.
- Temporary validation job: created once, invoked once, deleted successfully.
- Post-health database evidence: zero new canonical slots/attempts,
  ProductCandidates, ScanRuns, Daily OI runs, Daily Collection runs, and Dealer/GEX
  runs.
- Canonical Scheduler state after activation: three jobs, all ENABLED, correct New
  York schedules and canonical URIs, OIDC service account/audience correct, retry
  count zero. Radar next runs 2026-08-31; Dealer/GEX and Activity next run
  2026-08-28.
- Live GitHub default branch: automatic Radar/OI, Dealer/GEX, and Activity schedules
  absent; `workflow_dispatch` preserved; active scheduled-run count zero.
- Activation checkpoint: zero 2026-08-28 canonical slots, zero delivery attempts,
  zero network attempts, and zero consumed paid units.

No automated test, image validation, or infrastructure operation made a Nightwatch
request. Alembic `20260828_0020` was applied to the configured remote database.

## Cost-relevant inventory

Persistent resources are six API enablements, one Artifact Registry repository,
two Secret Manager containers with Founder-populated versions, two service
accounts, two secret-level grants, one scale-to-zero Cloud Run service, one
service-level invoker grant, and three enabled Scheduler jobs. No Cloud Build job or
staging bucket was created; both images were built locally. The one authorized
temporary Scheduler health job was invoked once and deleted; its maximum authorized
incremental billing exposure was USD 0.10.

Current official pricing states that Cloud Scheduler includes three free jobs per
billing account and otherwise costs USD 0.10/job/month; Cloud Run with no minimum
instances is usage-based; Secret Manager includes six active versions and 10,000
accesses monthly; Artifact Registry includes 0.5 GiB-month storage. Therefore the
declared fixed monthly amount is USD 0 when those account-level free tiers are
available. If none of the Scheduler or Secret Manager free allocation is
available, the three jobs plus two active secret versions are approximately USD
0.42/month, before Cloud Run execution, egress, image storage above 0.5 GiB, build,
logging, and vendor/API costs. Sources:
[Scheduler pricing](https://cloud.google.com/scheduler/pricing),
[Cloud Run pricing](https://cloud.google.com/run/pricing),
[Secret Manager pricing](https://cloud.google.com/secret-manager/pricing), and
[Artifact Registry pricing](https://cloud.google.com/artifact-registry/pricing).

## External contacts during this task

No Nightwatch endpoint was contacted. Google authentication and control-plane
contacts were limited to the authorized deployment through:

- `https://accounts.google.com/o/oauth2/auth`
- `https://oauth2.googleapis.com/`
- `https://cloudresourcemanager.googleapis.com/`
- `https://cloudbilling.googleapis.com/`
- `https://serviceusage.googleapis.com/`
- `https://artifactregistry.googleapis.com/`
- `https://secretmanager.googleapis.com/`
- `https://iam.googleapis.com/`
- `https://run.googleapis.com/`
- `https://cloudscheduler.googleapis.com/`
- `https://logging.googleapis.com/`
- `https://asia-northeast1-docker.pkg.dev/`
- `https://nightwatch-production-orchestrator-dtf5muscya-an.a.run.app/health`
- `https://api.github.com/`
- `https://github.com/lililinuk/options-anomaly-scanner.git`

Tool and image dependency contacts were:

- `https://dl.google.com/dl/cloudsdk/`
- `https://releases.hashicorp.com/terraform/`
- `https://registry.terraform.io/`
- `https://docker.io/`, `https://registry-1.docker.io/`, and
  `https://auth.docker.io/`
- `https://pypi.org/` and `https://files.pythonhosted.org/`

The configured database endpoint was contacted for one transactional migration and
revision verification:

- `postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432`

Official documentation/pricing pages consulted:

- `https://docs.cloud.google.com/scheduler/docs/reference/rest/v1/projects.locations.jobs`
- `https://docs.cloud.google.com/run/docs/triggering/using-scheduler`
- `https://docs.cloud.google.com/run/docs/securing/ingress`
- `https://docs.cloud.google.com/run/docs/authenticating/service-to-service`
- `https://docs.cloud.google.com/scheduler/docs/http-target-auth`
- `https://docs.cloud.google.com/scheduler/docs/creating`
- `https://docs.cloud.google.com/scheduler/docs/overview`
- `https://cloud.google.com/scheduler/pricing`
- `https://cloud.google.com/run/pricing`
- `https://cloud.google.com/secret-manager/pricing`
- `https://cloud.google.com/artifact-registry/pricing`

## First natural production proof

Pending. The natural 2026-08-28 Dealer/GEX and Activity slots must first be
evaluated against the Founder matrix. Activity is expected to fail closed if the
canonical Radar/OI evidence required for readiness is absent; that is truthful
behavior, not a migration failure. The next eligible XNYS session that naturally
receives all three slots is the first full-cycle proof. A zero-candidate COMPLETE
scan can prove the pipeline; it must not fabricate a Candidate or baseline.
Candidate-specific Stage 9 and baseline proof remains pending until a Candidate
naturally exists.

## Single next required Founder action

No Founder action is required at this checkpoint. Await the natural 2026-08-28
15:30 DEALER_GEX and 16:30 ACTIVITY_VNEXT executions, then inspect and append their
truthful production evidence without manually executing a canonical job.
