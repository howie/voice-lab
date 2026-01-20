# =============================================================================
# Artifact Registry Module Outputs
# =============================================================================

output "repository_id" {
  description = "ID of the Artifact Registry repository"
  value       = google_artifact_registry_repository.main.id
}

output "repository_name" {
  description = "Name of the Artifact Registry repository"
  value       = google_artifact_registry_repository.main.name
}

output "repository_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main.name}"
}
