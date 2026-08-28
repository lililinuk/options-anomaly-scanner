# Google Cloud canonical production scheduler

This package creates the required APIs, one Artifact Registry Docker repository,
two empty Secret Manager containers, one internal-ingress IAM-authenticated Cloud
Run service, and three paused-by-default Cloud Scheduler jobs. It does not create a
project, billing account, secret versions, or container image.

Required Founder-owned inputs:

- existing billing-enabled GCP project ID and region
- immutable Artifact Registry image digest built from `backend/Dockerfile`
- deployment identity authorized to manage the declared resources

Terraform intentionally never accepts or stores secret values. After the bootstrap
apply creates the empty containers, populate each first secret version through the
Google Cloud console or another secure Google Cloud path before deploying Cloud Run.

The runtime service account receives Secret Manager accessor on only those two
secrets. The scheduler service account receives only `roles/run.invoker` on this
Cloud Run service. Cloud Run ingress is internal-only; Scheduler must be in the same
project and uses the default `run.app` URL with OIDC audience equal to the service
URL. No `allUsers` binding is declared.

## Safe cutover

1. Apply Alembic revision `20260828_0020` before routing any scheduler request.
2. Build and push the image, pin its digest, and apply Terraform with
   `scheduler_jobs_paused=true`.
3. Verify Cloud Run revision health and authenticated non-paid routing at
   `/health`; do not manually invoke a canonical slot.
4. Choose the next market-day boundary. Do not cut over after any GitHub automatic
   slot for that market date has run.
5. In one reviewed change, remove the `schedule` blocks and scheduled-only jobs
   from the two GitHub workflows while preserving `workflow_dispatch`.
6. Apply `scheduler_jobs_paused=false` only after that workflow change is active.
7. Observe the first natural Scheduler cycle. Do not manufacture a Candidate.

The database canonical-slot unique key is the safety backstop for duplicate Google
deliveries. It is not a substitute for step 5 because historical GitHub runs do not
have Google canonical-slot identity.
