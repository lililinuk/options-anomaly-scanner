# Nightwatch Scanner vNext — Stage 8 Daily Automation Deployment Gate Report

Date: 2026-08-25  
Worktree: `F:\options-anomaly-scanner-stage8`  
Branch: `vnext/stage8-mag7-observation`  
Base HEAD: `3a63eaa1b9069d34199704fe31ac6466e8929d7d`

## 1. Result

```text
STAGE8_DAILY_AUTOMATION_GATE_RESULT=PASS_IMPLEMENTED_PENDING_PUSH
```

The rollover timing gate passed with a conservative production window. The minimum local workflow,
CLI orchestration, scheduler guards, and regressions were implemented. Nothing was committed,
pushed, dispatched, or deployed. GitHub scheduling therefore remains inactive for this local
change until a separately authorized commit/push reaches the branch from which GitHub schedules.

## 2. Scope and governing evidence

The execution package was preserved byte-for-byte at:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_EXECUTION_PACKAGE_20260825.md
SHA256=189E690039F429F9578862F52C1A33D3563C1737742D509B3913157A751F0EC3
```

All package-referenced governing evidence was read from the canonical evidence root. No governing
file was reconstructed from memory. The accepted Stage 8 working tree already contained four
intentional uncommitted remediation paths and they were preserved:

```text
backend/app/db/models.py
backend/app/scanner/v13.py
backend/tests/test_stage4b_phase2a_vnext.py
backend/tests/test_stage6_balanced_context.py
```

No unexpected pre-existing application diff was found.

## 3. Current workflow inventory

### Local Stage 8 worktree

| Workflow | Trigger and timezone | Entrypoint | Safety/write scope |
|---|---|---|---|
| Dealer/GEX archive | Weekdays 15:30 `America/New_York`; manual dispatch | `python -m app.cli capture-dealer-gex-archive --scheduled` | `contents: read`; server-side DB/API secrets; dedicated concurrency; XNYS guard; append-only Dealer/GEX archive writes; paid archive calls |
| OI-change rollover experiment | Ten UTC cron slots on weekdays; manual dry/live dispatch | `python -m app.research.oi_change_rollover probe` | `contents: read`, `actions: read`; isolated artifacts; no runtime DB; date-bounded experiment calls |
| Phase 2A daily archive and vNext observation | Weekdays 06:30 and 16:30 `America/New_York`; manual collection-only dispatch | `archive-mag7-daily` and `run-daily-vnext-observation` | `contents: read`; server-side secrets; one concurrency group; XNYS/source gates; no automatic retry |

### Actual GitHub default-branch state inspected

The active GitHub workflows were Dealer/GEX archive and the rollover experiment. The Phase 2A
workflow in this Stage 8 worktree was not present as an active workflow on the inspected default
branch. The local changes in this report are not deployed.

```text
CURRENT_WORKFLOWS=LOCAL_STAGE8:dealer-gex-archive.yml,oi-change-rollover-timing-experiment.yml,phase2a-daily-archive.yml; GITHUB_ACTIVE_DEFAULT_BRANCH:dealer-gex-archive.yml,oi-change-rollover-timing-experiment.yml
DEALER_GEX_WORKFLOW_PATH=F:\options-anomaly-scanner-stage8\.github\workflows\dealer-gex-archive.yml
ROLLOVER_EXPERIMENT_WORKFLOW_PATH=F:\options-anomaly-scanner-stage8\.github\workflows\oi-change-rollover-timing-experiment.yml
PHASE2A_DAILY_ARCHIVE_WORKFLOW_PATH=F:\options-anomaly-scanner-stage8\.github\workflows\phase2a-daily-archive.yml
DAILY_VNEXT_OBSERVATION_WORKFLOW_PATH=F:\options-anomaly-scanner-stage8\.github\workflows\phase2a-daily-archive.yml#daily-vnext-observation
```

Stage 4A workflow plumbing existed locally but Radar/OI scheduling was intentionally inactive
pending rollover evidence. This gate supplies that evidence and activates the local schedule.

## 4. Rollover timing gate

Read-only GitHub inspection covered 50 successful scheduled experiment runs from 2026-08-18
through 2026-08-24. The downloaded safe artifacts contained 150 ticker-probe records across AAPL,
NVDA, and TSLA. All vendor responses recorded HTTP 200, with zero retries and no contradictory
ticker dates within a probe.

| Expected completed XNYS session | Earliest observed all-ticker expected date (ET) | Last observed expected date (ET) | First observed later/ahead date (ET) |
|---|---:|---:|---:|
| 2026-08-17 | 2026-08-18 05:25:26 | 08:30:22 | 09:37:09 |
| 2026-08-18 | 2026-08-19 05:26:34 | 09:38:45 | 10:02:04 |
| 2026-08-19 | 2026-08-20 05:26:21 | 09:40:31 | 10:04:52 |
| 2026-08-20 | 2026-08-21 05:29:16 | 08:32:19 | 09:39:34 |
| 2026-08-21 | 2026-08-24 05:39:39 | 08:34:06 | 09:44:26 |

The Monday evidence correctly resolved Friday as the previous completed XNYS session. No calendar
day substitution was used. The earliest actual successful probe across the five experiment days was
05:25 ET; the latest first availability was 05:39 ET; and the earliest observed vendor switch was
09:37 ET. A 06:00–08:00 ET production window is therefore conservative. The cron is placed at
06:30 ET, not at the edge of the evidence.

The scheduled Radar/OI CLI now also checks XNYS eligibility and the 06:00–08:00 ET window before
creating a Nightwatch client. A delayed run after 08:00, a run before 06:00, a weekend, or an XNYS
holiday is skipped before any paid request. Manual dispatch remains collection-only and is not
silently converted into a scan.

```text
ROLLOVER_TIMING_GATE=PASS_WITH_CONSERVATIVE_SAFE_WINDOW
RADAR_OI_PRODUCTION_SAFE_WINDOW=06:00-08:00 America/New_York
RADAR_OI_SCHEDULE_TIMEZONE=America/New_York
RADAR_OI_SCHEDULE_EVIDENCE_BASIS=50 successful scheduled runs; 150 AAPL/NVDA/TSLA records; five expected XNYS dates; all-ticker agreement; HTTP 200; retries 0; latest first availability 05:39:39 ET; earliest observed switch 09:37:09 ET; no contradictions
```

## 5. Implemented daily chain

The local workflow uses one multi-job file with two source-time schedules:

1. At 06:30 ET, `radar-oi-archive` runs the accepted Phase 2A `radar-oi` mode. That mode first runs
   the full Daily OI archive and then Radar/OI evaluation, thereby accumulating Contract OI history
   used by accepted Persistence analytics.
2. At 16:30 ET, `activity-archive` runs the accepted session-complete Activity mode. The existing
   XNYS close guard remains authoritative, including early-close and non-trading behavior.
3. The `daily-vnext-observation` job has an explicit `needs: activity-archive` edge and runs only for
   the scheduled 16:30 event. It never runs from `workflow_dispatch`.
4. Before the scan, the backend readiness gate requires all seven configured MAG7 tickers to have:
   current-market-date `ACTIVITY` COMPLETE coverage, prior-completed-XNYS-session `RADAR` COMPLETE
   coverage, and successful Daily OI archive ticker evidence for that same vendor OI date.
5. The gate also refuses any second scheduled scan for the same NY market date, regardless of the
   first scheduled run's terminal state. This preserves the no-blind-paid-retry rule.
6. Exactly one accepted `app.scanner.v13.Mag7Scanner` invocation runs with `max_retries=0`, the
   configured MAG7 universe, and all accepted thresholds/scoring unchanged.
7. On `COMPLETE`, persisted ProductCandidates for that ScanRun are loaded. The accepted
   `Stage6BalancedContextService.create_baseline(candidate.id)` is called once per candidate without
   a source client, so it uses archived evidence only and cannot run paid REFRESH. The service
   enforces `evidence_cutoff_at = candidate_first_knowledge_at` and the accepted JSONB SQL-NULL ORM.
8. `COMPLETE` with zero candidates becomes orchestration state `SUCCESS_NO_CANDIDATE`; `PARTIAL` or
   `FAILED` never enters baseline creation and returns a non-success workflow exit code.

```text
PHASE2A_DAILY_ARCHIVE_ENTRYPOINT=python -m app.cli archive-mag7-daily --mode <radar-oi|activity> --scheduled
VNEXT_MAG7_PRODUCTION_ENTRYPOINT=python -m app.cli run-daily-vnext-observation -> app.scanner.v13.Mag7Scanner.execute(trigger="scheduled_daily")
FIRST_KNOWLEDGE_BASELINE_ENTRYPOINT=app.confirmation.vnext.Stage6BalancedContextService.create_baseline(product_candidate_id)
WORKFLOW_TOPOLOGY=ONE_MULTI_JOB_WORKFLOW_WITH_TWO_SOURCE_TIME_SCHEDULES_AND_PERSISTED_EVIDENCE_DEPENDENCY_GATE
RATIONALE=Morning and post-close sources remain failure-isolated; the post-close scan has an explicit Activity job dependency and a cross-run persisted-evidence gate for morning Radar/OI and Daily OI; manual collection dispatch cannot trigger a scan; same-day scheduled retries are refused.
DAILY_AUTOMATION_DEPENDENCY_ORDER=06:30 ET Daily OI archive -> Radar/OI evaluation -> 16:30 ET session-complete Activity -> seven-ticker persisted-source readiness gate -> exactly one vNext MAG7 scan -> immutable ProductCandidate/triggers -> one FIRST_KNOWLEDGE_BASELINE per candidate -> Stage 7 persisted-result reads
DAILY_SCAN_EARLIEST_SAFE_START=16:30 America/New_York AND only after actual XNYS session close and all persisted source gates pass
DAILY_SCAN_TIMEZONE=America/New_York
EXPECTED_DAILY_MAG7_PAID_UNITS=14
MAX_CONFIGURED_DAILY_MAG7_PAID_UNITS=75
```

The expected 14 scan units are supported by the production fan-out and the three controlled Stage 8
observations. The configured scanner ceiling remains 75; this gate did not invent or change a
financial/cost threshold. Source archive costs are separate from the vNext scan figure.

## 6. Failure and integrity semantics

The implemented behavior preserves:

```text
SKIPPED_NON_TRADING_SESSION=scheduled Radar/OI exits before client creation; Activity keeps its accepted XNYS guard
SKIPPED_BEFORE_SOURCE_READY=scheduled Radar/OI before 06:00 exits before client creation; scan readiness failures exit before scanner invocation
SKIPPED_AFTER_SAFE_WINDOW=delayed scheduled Radar/OI after 08:00 exits before client creation
SUCCESS=COMPLETE scan with one or more candidates and one baseline per candidate
SUCCESS_NO_CANDIDATE=COMPLETE scan with zero ProductCandidates and zero baselines
PARTIAL=truthful scan terminal state; no baseline success is fabricated
FAILED=truthful failure; no baseline success is fabricated
```

No candidate, trigger, source, or historical row is altered by the readiness check. Missing ticker
coverage fails the gate; it is not treated as a numeric zero. Candidate materialization remains in
the accepted scanner completion path and occurs before optional Deep-Dive availability can suppress
candidate existence. Baseline creation does not mutate `candidate_first_knowledge_at` or triggers.

## 7. O1 / O4 / O6 automation coverage

### O1 — Candidates/day

Each eligible NY market day can produce one scheduled ScanRun. Persisted ScanRun terminal state and
ProductCandidate occurrences distinguish candidate-producing success, genuine zero-candidate
success, PARTIAL, and FAILED. Same-day automatic paid retries are prevented.

### O4 — Persistence maturation

The morning `radar-oi` mode runs the accepted Daily OI archiver before Radar. Successful archive
ticker evidence is required by the evening scan gate. Append-only Contract OI snapshots therefore
accumulate valid observation history naturally; accepted 3/5/10 anchors may mature without a new
freshness threshold being invented. Missing or incomplete history remains missing/immature.

### O6 — Ticker concentration

The accepted fixed MAG7 universe is unchanged. ProductCandidate occurrences and immutable triggers
remain keyed to each ScanRun/NY market date/ticker, supporting occurrence and candidate-day counts
and ticker trigger shares across dates. No universe expansion or concentration threshold was added.

```text
O1_AUTOMATION_COVERAGE=YES
O4_AUTOMATION_COVERAGE=YES
O6_AUTOMATION_COVERAGE=YES
```

## 8. Dashboard visibility

The accepted Stage 7 dashboard/API already exposes the required truthful fields: last successful
Phase 2A collection/date, latest scan status/time, candidate date, baseline existence, quota facts,
and observation age. It does not separately expose every Phase 2A subjob's latest status, but that
is not required to establish the listed Stage 8 dashboard visibility fields and no Stage 7 redesign
was authorized.

```text
DASHBOARD_AUTOMATION_VISIBILITY_GAP=NONE_FOR_REQUIRED_FIELDS; source-specific Phase2A subjob status remains a carried operator-visibility limitation
```

## 9. Authorized files and changes

```text
AUTHORIZED_FILES_IMPLEMENTED:
- .github/workflows/phase2a-daily-archive.yml: activate evidence-backed schedules and ordered jobs
- backend/app/cli.py: scheduler-safe entrypoint and pre-client Radar/OI guard
- backend/app/scanner/daily.py: truthful persisted schedule provenance only
- backend/app/scanner/daily_semantics.py: pure XNYS/evidence-window Radar/OI schedule plan
- backend/app/scanner/daily_observation.py: persisted-source readiness gate and one-scan/baseline orchestration
- backend/tests/test_phase2a_daily_workflow.py: replace superseded pending-rollover assertions
- backend/tests/test_daily_vnext_observation.py: readiness, no-retry, terminal-state, baseline, and schedule guards
- backend/tests/test_stage8_daily_automation_workflow.py: workflow topology and accepted-remediation regressions
- docs/evidence/stage8/NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md: sanitized report
```

Task-specific change counts, excluding the four accepted pre-existing Stage 8 remediation paths:

```text
APPLICATION_CODE_CHANGES=4 files; 258 additions, 9 deletions
TEST_CODE_CHANGES=3 files; 233 additions, 5 deletions
WORKFLOW_FILES_CHANGED=1 file; 110 additions, 5 deletions
MIGRATION_CHANGES=0
```

No scanner scoring, candidate projection, Deep-Dive budget, universe, retry fan-out, schema, model
constraint, workflow secret, dashboard, or Forward Outcome logic was changed.

## 10. Verification

All verification was offline with the autouse no-live-Nightwatch test guard active.

```text
Focused new workflow/orchestration tests=15 passed
Stage 4A/4B/5/6/7 plus new focused matrix=passed
Pre-existing workflow regression matrix=passed
Full backend suite=397 passed
Ruff=PASS
Alembic heads=20260818_0017 (single head)
git diff --check=PASS
sanitized secret scan=PASS
Frontend ESLint=PASS
Frontend Stage 7 regressions=13 passed
Frontend glossary check=PASS (34 governed vNext concepts)
Frontend production build=PASS
Actionlint=UNAVAILABLE; repository static workflow validations and full tests passed
```

The frontend dependency install used the lockfile, reported 0 vulnerabilities, and generated
`node_modules`/`.next` artifacts were removed after verification.

## 11. External contact ledger

No Nightwatch endpoint and no runtime database endpoint was contacted. Read-only evidence retrieval
contacted:

```text
https://github.com/lililinuk/options-anomaly-scanner.git
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/workflows/335910966/runs
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/runs/{run_id}/artifacts (50 inspected scheduled runs)
https://api.github.com/repos/lililinuk/options-anomaly-scanner/actions/artifacts/{artifact_id}/zip (safe rollover artifacts)
https://registry.npmjs.org/ (locked frontend dependency installation)
```

No credentials, full database URL, or API key was printed or stored in this report.

## 12. Authorization ledger and required fields

```text
STAGE8_DAILY_AUTOMATION_GATE_RESULT=PASS_IMPLEMENTED_PENDING_PUSH

CURRENT_WORKFLOWS=LOCAL_STAGE8:dealer-gex-archive.yml,oi-change-rollover-timing-experiment.yml,phase2a-daily-archive.yml; GITHUB_ACTIVE_DEFAULT_BRANCH:dealer-gex-archive.yml,oi-change-rollover-timing-experiment.yml
PHASE2A_DAILY_ARCHIVE_WORKFLOW_PATH=F:\options-anomaly-scanner-stage8\.github\workflows\phase2a-daily-archive.yml
DAILY_VNEXT_OBSERVATION_WORKFLOW_PATH=F:\options-anomaly-scanner-stage8\.github\workflows\phase2a-daily-archive.yml#daily-vnext-observation

ROLLOVER_TIMING_GATE=PASS_WITH_CONSERVATIVE_SAFE_WINDOW
RADAR_OI_PRODUCTION_SAFE_WINDOW=06:00-08:00 America/New_York
RADAR_OI_SCHEDULE_TIMEZONE=America/New_York
RADAR_OI_SCHEDULE_EVIDENCE_BASIS=50 successful scheduled runs; 150 records; five expected XNYS dates; all-ticker agreement; zero HTTP/retry contradictions

PHASE2A_DAILY_ARCHIVE_ENTRYPOINT=python -m app.cli archive-mag7-daily --mode <radar-oi|activity> --scheduled
VNEXT_MAG7_PRODUCTION_ENTRYPOINT=python -m app.cli run-daily-vnext-observation -> app.scanner.v13.Mag7Scanner.execute(trigger="scheduled_daily")
FIRST_KNOWLEDGE_BASELINE_ENTRYPOINT=app.confirmation.vnext.Stage6BalancedContextService.create_baseline(product_candidate_id)

WORKFLOW_TOPOLOGY=ONE_MULTI_JOB_WORKFLOW_WITH_TWO_SOURCE_TIME_SCHEDULES_AND_PERSISTED_EVIDENCE_DEPENDENCY_GATE
DAILY_AUTOMATION_DEPENDENCY_ORDER=06:30 ET Daily OI -> Radar/OI -> 16:30 ET session-complete Activity -> source readiness -> one vNext scan -> candidates/triggers -> one baseline per candidate -> dashboard
DAILY_SCAN_EARLIEST_SAFE_START=16:30 America/New_York AND after actual XNYS close/source readiness
DAILY_SCAN_TIMEZONE=America/New_York

EXPECTED_DAILY_MAG7_PAID_UNITS=14
MAX_CONFIGURED_DAILY_MAG7_PAID_UNITS=75

O1_AUTOMATION_COVERAGE=YES
O4_AUTOMATION_COVERAGE=YES
O6_AUTOMATION_COVERAGE=YES
DASHBOARD_AUTOMATION_VISIBILITY_GAP=NONE_FOR_REQUIRED_FIELDS; source-specific Phase2A subjob status remains carried

APPLICATION_CODE_CHANGES=4
TEST_CODE_CHANGES=3
WORKFLOW_FILES_CHANGED=1
MIGRATION_CHANGES=0

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_APPLICATION_DATA_WRITES=0
REMOTE_SCHEMA_WRITES=0
WORKFLOWS_DISPATCHED=0

COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

PRIMARY_REPORT_PATH=F:\options-anomaly-scanner-stage8\docs\evidence\stage8\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md
CANONICAL_REPORT_PATH=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_DAILY_AUTOMATION_DEPLOYMENT_GATE_REPORT_20260825.md
REPORT_BACKUP_BYTE_IDENTICAL=VERIFIED_AFTER_WRITE

DAILY_AUTOMATION_DEPLOYED_TO_GITHUB=NO
NEXT_AUTHORIZED_STAGE=NONE
```

STOP. No workflow was dispatched, no scan was run, and no subsequent stage was started.
