# =============================================================================
# Voice Lab GCP Terraform Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# Cloud Run Service URLs
# -----------------------------------------------------------------------------

output "backend_url" {
  description = "URL of the backend Cloud Run service"
  value       = module.cloud_run.backend_url
}

output "frontend_url" {
  description = "URL of the frontend Cloud Run service"
  value       = module.cloud_run.frontend_url
}

output "backend_custom_domain" {
  description = "Custom domain for the backend API"
  value       = var.custom_domain != "" ? "https://${var.api_subdomain}.${var.custom_domain}" : null
}

output "frontend_custom_domain" {
  description = "Custom domain for the frontend"
  value       = var.custom_domain != "" ? "https://${var.custom_domain}" : null
}

# -----------------------------------------------------------------------------
# Database Connection
# -----------------------------------------------------------------------------

output "database_connection_name" {
  description = "Cloud SQL instance connection name"
  value       = module.cloud_sql.connection_name
}

output "database_private_ip" {
  description = "Private IP address of Cloud SQL instance"
  value       = module.cloud_sql.private_ip
  sensitive   = true
}

output "database_name" {
  description = "Name of the database"
  value       = module.cloud_sql.database_name
}

output "database_user" {
  description = "Database username"
  value       = module.cloud_sql.database_user
}

# -----------------------------------------------------------------------------
# Networking
# -----------------------------------------------------------------------------

output "vpc_network_id" {
  description = "ID of the VPC network"
  value       = module.networking.vpc_id
}

output "vpc_connector_id" {
  description = "ID of the VPC Access Connector"
  value       = module.networking.connector_id
}

# -----------------------------------------------------------------------------
# IAM
# -----------------------------------------------------------------------------

output "service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = module.iam.cloud_run_service_account_email
}

# -----------------------------------------------------------------------------
# Storage
# -----------------------------------------------------------------------------

output "audio_bucket_name" {
  description = "Name of the audio storage bucket"
  value       = module.storage.audio_bucket_name
}

output "audio_bucket_url" {
  description = "URL of the audio storage bucket"
  value       = module.storage.audio_bucket_url
}

# -----------------------------------------------------------------------------
# Artifact Registry
# -----------------------------------------------------------------------------

output "artifact_registry_url" {
  description = "URL of the Artifact Registry repository"
  value       = module.artifact_registry.repository_url
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
  value = var.custom_domain != "" ? join("\n", [
    "Frontend: ${var.custom_domain} -> CNAME -> ghs.googleusercontent.com (proxied: false)",
    "Backend:  ${var.api_subdomain}.${var.custom_domain} -> CNAME -> ghs.googleusercontent.com (proxied: false)"
  ]) : "No custom domain configured"
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
