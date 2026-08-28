variable "project_id" {
  description = "Existing billing-enabled Google Cloud project ID."
  type        = string
  nullable    = false
}

variable "region" {
  description = "Founder-selected Google Cloud region for Cloud Run and Cloud Scheduler."
  type        = string
  nullable    = false
}

variable "container_image" {
  description = "Immutable Artifact Registry image digest for the scheduler service."
  type        = string
  nullable    = false

  validation {
    condition     = strcontains(var.container_image, "@sha256:")
    error_message = "container_image must be pinned by sha256 digest."
  }
}

variable "artifact_repository_id" {
  description = "Artifact Registry Docker repository created for the orchestration image."
  type        = string
  default     = "nightwatch-production"
}

variable "database_url_secret_id" {
  description = "Secret Manager container created for DATABASE_URL; Terraform never manages secret values."
  type        = string
  default     = "nightwatch-database-url"
}

variable "nightwatch_api_key_secret_id" {
  description = "Secret Manager container created for NIGHTWATCH_API_KEY; Terraform never manages secret values."
  type        = string
  default     = "nightwatch-api-key"
}

variable "scheduler_jobs_paused" {
  description = "Keep true until the explicit atomic cutover boundary."
  type        = bool
  default     = true
}

variable "service_name" {
  type    = string
  default = "nightwatch-production-orchestrator"
}

variable "scheduler_job_radar_oi" {
  type    = string
  default = "nightwatch-radar-oi"
}

variable "scheduler_job_dealer_gex" {
  type    = string
  default = "nightwatch-dealer-gex"
}

variable "scheduler_job_activity_vnext" {
  type    = string
  default = "nightwatch-activity-vnext"
}
