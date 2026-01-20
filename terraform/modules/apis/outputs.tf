# =============================================================================
# APIs Module Outputs
# =============================================================================

output "enabled_apis" {
  description = "List of enabled APIs"
  value       = [for api in google_project_service.apis : api.service]
}

output "api_ready" {
  description = "Signal that APIs are ready"
  value       = time_sleep.api_propagation.id
}
