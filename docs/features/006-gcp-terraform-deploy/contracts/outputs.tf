# =============================================================================
# Voice Lab GCP Terraform Outputs Contract
# =============================================================================
# This file defines the output values from the Voice Lab GCP deployment.
# =============================================================================

# -----------------------------------------------------------------------------
# Cloud Run Service URLs
# -----------------------------------------------------------------------------

output "backend_url" {
  description = "URL of the backend Cloud Run service"
  value       = "google_cloud_run_v2_service.backend.uri"
}

output "frontend_url" {
  description = "URL of the frontend Cloud Run service"
  value       = "google_cloud_run_v2_service.frontend.uri"
}

output "backend_custom_domain" {
  description = "Custom domain for the backend API"
  value       = "var.custom_domain != \"\" ? \"https://${var.api_subdomain}.${var.custom_domain}\" : null"
}

output "frontend_custom_domain" {
  description = "Custom domain for the frontend"
  value       = "var.custom_domain != \"\" ? \"https://${var.custom_domain}\" : null"
}

# -----------------------------------------------------------------------------
# Database Connection
# -----------------------------------------------------------------------------

output "database_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = "google_sql_database_instance.main.connection_name"
}

output "database_private_ip" {
  description = "Private IP address of Cloud SQL instance"
  value       = "google_sql_database_instance.main.private_ip_address"
  sensitive   = true
}

output "database_name" {
  description = "Name of the database"
  value       = "google_sql_database.main.name"
}

output "database_user" {
  description = "Database username"
  value       = "google_sql_user.main.name"
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------

output "vpc_network_id" {
  description = "ID of the VPC network"
  value       = "google_compute_network.vpc.id"
}

output "vpc_connector_id" {
  description = "ID of the VPC Access Connector"
  value       = "google_vpc_access_connector.main.id"
}

# -----------------------------------------------------------------------------
# IAM
# -----------------------------------------------------------------------------

output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = "google_service_account.cloud_run.email"
}

# -----------------------------------------------------------------------------
# Storage
# -----------------------------------------------------------------------------

output "audio_bucket_name" {
  description = "Name of the audio storage bucket"
  value       = "google_storage_bucket.audio.name"
}

output "audio_bucket_url" {
  description = "URL of the audio storage bucket"
  value       = "google_storage_bucket.audio.url"
}

output "tf_state_bucket_name" {
  description = "Name of the Terraform state bucket"
  value       = "google_storage_bucket.tf_state.name"
}

# -----------------------------------------------------------------------------
# Artifact Registry
# -----------------------------------------------------------------------------

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/voice-lab"
}

# -----------------------------------------------------------------------------
# DNS Configuration (for Cloudflare setup)
# -----------------------------------------------------------------------------

output "cloudflare_cname_target" {
  description = "CNAME target for Cloudflare DNS records"
  value       = "ghs.googleusercontent.com"
}

output "required_dns_records" {
  description = "DNS records to create in Cloudflare"
  value = <<-EOT
    Frontend: ${var.custom_domain} -> CNAME -> ghs.googleusercontent.com (proxied: false)
    Backend:  ${var.api_subdomain}.${var.custom_domain} -> CNAME -> ghs.googleusercontent.com (proxied: false)
  EOT
}

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

output "deployment_summary" {
  description = "Summary of the deployment"
  value = <<-EOT
    Voice Lab GCP Deployment Summary
    ================================
    Project ID: ${var.project_id}
    Region: ${var.region}
    Environment: ${var.environment}

    Services:
    - Backend: ${var.custom_domain != "" ? "https://${var.api_subdomain}.${var.custom_domain}" : "see backend_url output"}
    - Frontend: ${var.custom_domain != "" ? "https://${var.custom_domain}" : "see frontend_url output"}

    Database:
    - Instance: voice-lab-postgres
    - Type: PostgreSQL 16
    - Tier: ${var.db_tier}

    Authentication:
    - Provider: Google OAuth 2.0
    - Allowed Domains: ${join(", ", var.allowed_domains)}

    Cost Optimization:
    - Backend Min Instances: ${var.backend_min_instances}
    - Frontend Min Instances: ${var.frontend_min_instances}
    - (Set to 0 for pay-per-request billing)
  EOT
}
