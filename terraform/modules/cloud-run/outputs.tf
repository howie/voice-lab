# =============================================================================
# Cloud Run Module Outputs
# =============================================================================

output "backend_url" {
  description = "URL of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "backend_name" {
  description = "Name of the backend Cloud Run service"
  value       = google_cloud_run_v2_service.backend.name
}

output "frontend_url" {
  description = "URL of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "frontend_name" {
  description = "Name of the frontend Cloud Run service"
  value       = google_cloud_run_v2_service.frontend.name
}

output "backend_domain_mapping_status" {
  description = "Status of backend domain mapping"
  value       = var.custom_domain != "" ? google_cloud_run_domain_mapping.backend[0].status : null
}

output "frontend_domain_mapping_status" {
  description = "Status of frontend domain mapping"
  value       = var.custom_domain != "" ? google_cloud_run_domain_mapping.frontend[0].status : null
}
