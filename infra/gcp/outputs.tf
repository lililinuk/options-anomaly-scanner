output "artifact_registry_repository" {
  value = google_artifact_registry_repository.orchestrator.name
}

output "artifact_registry_image_prefix" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.orchestrator.repository_id}"
}

output "database_url_secret_id" {
  value = google_secret_manager_secret.database_url.secret_id
}

output "nightwatch_api_key_secret_id" {
  value = google_secret_manager_secret.nightwatch_api_key.secret_id
}

output "cloud_run_service_name" {
  value = google_cloud_run_v2_service.orchestrator.name
}

output "cloud_run_service_uri" {
  value = google_cloud_run_v2_service.orchestrator.uri
}

output "scheduler_job_names" {
  value = { for slot, job in google_cloud_scheduler_job.canonical : slot => job.name }
}

output "scheduler_jobs_paused" {
  value = var.scheduler_jobs_paused
}
