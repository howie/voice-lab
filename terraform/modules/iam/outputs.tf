# =============================================================================
# IAM Module Outputs
# =============================================================================

output "cloud_run_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloud_run.email
}

output "cloud_run_service_account_id" {
  description = "ID of the Cloud Run service account"
  value       = google_service_account.cloud_run.id
}

output "cloud_build_service_account_email" {
  description = "Email of the Cloud Build service account"
  value       = var.create_build_service_account ? google_service_account.cloud_build[0].email : null
}
