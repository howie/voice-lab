# =============================================================================
# Cloud Run Module Variables
# =============================================================================

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
}

variable "environment" {
  type        = string
  description = "Environment name"
}

variable "service_account_email" {
  type        = string
  description = "Service account email for Cloud Run services"
}

variable "vpc_connector_id" {
  type        = string
  description = "VPC Access Connector ID"
}

# Backend configuration
variable "backend_image" {
  type        = string
  description = "Docker image for backend service"
}

variable "backend_cpu" {
  type        = string
  description = "CPU allocation for backend"
  default     = "1"
}

variable "backend_memory" {
  type        = string
  description = "Memory allocation for backend"
  default     = "512Mi"
}

variable "backend_min_instances" {
  type        = number
  description = "Minimum instances for backend"
  default     = 0
}

variable "backend_max_instances" {
  type        = number
  description = "Maximum instances for backend"
  default     = 10
}

# Frontend configuration
variable "frontend_image" {
  type        = string
  description = "Docker image for frontend service"
}

variable "frontend_cpu" {
  type        = string
  description = "CPU allocation for frontend"
  default     = "1"
}

variable "frontend_memory" {
  type        = string
  description = "Memory allocation for frontend"
  default     = "256Mi"
}

variable "frontend_min_instances" {
  type        = number
  description = "Minimum instances for frontend"
  default     = 0
}

variable "frontend_max_instances" {
  type        = number
  description = "Maximum instances for frontend"
  default     = 5
}

# Database configuration
variable "database_connection_name" {
  type        = string
  description = "Cloud SQL connection name"
}

variable "database_host" {
  type        = string
  description = "Database host (private IP)"
}

variable "database_name" {
  type        = string
  description = "Database name"
}

variable "database_user" {
  type        = string
  description = "Database user"
}

variable "database_password_secret" {
  type        = string
  description = "Secret ID for database password"
}

# Secrets
variable "oauth_client_id_secret" {
  type        = string
  description = "Secret ID for OAuth Client ID"
}

variable "oauth_client_secret_secret" {
  type        = string
  description = "Secret ID for OAuth Client Secret"
}

variable "openai_api_key_secret" {
  type        = string
  description = "Secret ID for OpenAI API Key"
  default     = null
}

# Application config
variable "allowed_domains" {
  type        = list(string)
  description = "Allowed email domains for OAuth"
}

variable "audio_bucket" {
  type        = string
  description = "Audio storage bucket name"
}

variable "custom_domain" {
  type        = string
  description = "Custom domain for the application"
  default     = ""
}

variable "api_subdomain" {
  type        = string
  description = "API subdomain"
  default     = "api"
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply to resources"
  default     = {}
}

variable "additional_cors_origins" {
  type        = list(string)
  description = "Additional CORS origins to allow (e.g., Cloud Run direct URLs)"
  default     = []
}
