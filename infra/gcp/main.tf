locals {
  scheduler_jobs = {
    RADAR_OI = {
      name     = var.scheduler_job_radar_oi
      schedule = "30 6 * * 1-5"
    }
    DEALER_GEX = {
      name     = var.scheduler_job_dealer_gex
      schedule = "30 15 * * 1-5"
    }
    ACTIVITY_VNEXT = {
      name     = var.scheduler_job_activity_vnext
      schedule = "30 16 * * 1-5"
    }
  }
}

resource "google_project_service" "required" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "orchestrator" {
  project       = var.project_id
  location      = var.region
  repository_id = var.artifact_repository_id
  description   = "Nightwatch canonical production orchestration images"
  format        = "DOCKER"

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret" "database_url" {
  project   = var.project_id
  secret_id = var.database_url_secret_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret" "nightwatch_api_key" {
  project   = var.project_id
  secret_id = var.nightwatch_api_key_secret_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.required]
}

resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = "nightwatch-prod-runtime"
  display_name = "Nightwatch production orchestrator runtime"

  depends_on = [google_project_service.required]
}

resource "google_service_account" "scheduler_invoker" {
  project      = var.project_id
  account_id   = "nightwatch-scheduler-invoker"
  display_name = "Nightwatch Cloud Scheduler invoker"

  depends_on = [google_project_service.required]
}

resource "google_secret_manager_secret_iam_member" "database_url" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_secret_manager_secret_iam_member" "nightwatch_api_key" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.nightwatch_api_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service" "orchestrator" {
  project             = var.project_id
  name                = var.service_name
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_INTERNAL_ONLY"
  deletion_protection = true

  template {
    service_account                  = google_service_account.runtime.email
    timeout                          = "1800s"
    max_instance_request_concurrency = 1

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      image = var.container_image

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = true
      }

      env {
        name  = "APP_ENV"
        value = "production"
      }

      env {
        name  = "NIGHTWATCH_MAX_RETRIES"
        value = "0"
      }

      env {
        name  = "GCP_SCHEDULER_JOB_RADAR_OI"
        value = var.scheduler_job_radar_oi
      }

      env {
        name  = "GCP_SCHEDULER_JOB_DEALER_GEX"
        value = var.scheduler_job_dealer_gex
      }

      env {
        name  = "GCP_SCHEDULER_JOB_ACTIVITY_VNEXT"
        value = var.scheduler_job_activity_vnext
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.database_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "NIGHTWATCH_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.nightwatch_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_secret_manager_secret_iam_member.database_url,
    google_secret_manager_secret_iam_member.nightwatch_api_key,
  ]
}

resource "google_cloud_run_v2_service_iam_member" "scheduler_invoker" {
  project  = var.project_id
  location = google_cloud_run_v2_service.orchestrator.location
  name     = google_cloud_run_v2_service.orchestrator.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler_invoker.email}"
}

resource "google_cloud_scheduler_job" "canonical" {
  for_each = local.scheduler_jobs

  name             = each.value.name
  project          = var.project_id
  description      = "Nightwatch canonical ${each.key} production slot"
  schedule         = each.value.schedule
  time_zone        = "America/New_York"
  region           = var.region
  paused           = var.scheduler_jobs_paused
  attempt_deadline = "1800s"

  retry_config {
    retry_count          = 0
    max_retry_duration   = "0s"
    min_backoff_duration = "5s"
    max_backoff_duration = "5s"
  }

  http_target {
    uri         = "${google_cloud_run_v2_service.orchestrator.uri}/canonical-slots/${each.key}"
    http_method = "POST"
    headers = {
      "Content-Type" = "application/json"
    }
    body = base64encode("{}")

    oidc_token {
      service_account_email = google_service_account.scheduler_invoker.email
      audience              = google_cloud_run_v2_service.orchestrator.uri
    }
  }

  depends_on = [google_cloud_run_v2_service_iam_member.scheduler_invoker]
}
