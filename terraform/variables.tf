# =============================================================================
# Voice Lab GCP Terraform Variables
# =============================================================================
# This file defines the input variables for the Voice Lab GCP deployment.
# Copy terraform.tfvars.example to terraform.tfvars and fill in your values.
# =============================================================================

# -----------------------------------------------------------------------------
# Project Configuration
# -----------------------------------------------------------------------------

variable "project_id" {
  type        = string
  description = "GCP Project ID where resources will be created"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Project ID must be 6-30 characters, start with a letter, and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "region" {
  type        = string
  description = "GCP region for resource deployment"
  default     = "asia-east1"

  validation {
    condition     = contains(["asia-east1", "asia-northeast1", "us-central1", "us-west1", "europe-west1"], var.region)
    error_message = "Region must be one of: asia-east1, asia-northeast1, us-central1, us-west1, europe-west1."
  }
}

variable "environment" {
  type        = string
  description = "Environment name (e.g., test, staging, prod)"
  default     = "test"

  validation {
    condition     = contains(["test", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: test, staging, prod."
  }
}

# -----------------------------------------------------------------------------
# Authentication & Domain Configuration
# -----------------------------------------------------------------------------

variable "allowed_domains" {
  type        = list(string)
  description = "List of allowed Google Workspace/Gmail domains for OAuth login"
  default     = ["heyuai.com.tw"]

  validation {
    condition     = length(var.allowed_domains) > 0
    error_message = "At least one allowed domain must be specified."
  }
}

variable "custom_domain" {
  type        = string
  description = "Custom domain for the Voice Lab application (e.g., voice-lab.heyuai.com.tw)"
  default     = ""
}

variable "api_subdomain" {
  type        = string
  description = "Subdomain for the API endpoint (e.g., api)"
  default     = "api"
}

variable "frontend_subdomain" {
  type        = string
  description = "Subdomain for the frontend (used in Cloudflare DNS record name, e.g., voice-lab)"
  default     = "voice-lab"
}

# -----------------------------------------------------------------------------
# Cloudflare Configuration
# -----------------------------------------------------------------------------

variable "cloudflare_api_token" {
  type        = string
  description = "Cloudflare API token with DNS edit permissions"
  sensitive   = true
  default     = ""
}

variable "cloudflare_zone_id" {
  type        = string
  description = "Cloudflare Zone ID for the domain"
  default     = ""
}

# -----------------------------------------------------------------------------
# Cloud SQL Configuration
# -----------------------------------------------------------------------------

variable "db_tier" {
  type        = string
  description = "Cloud SQL instance tier"
  default     = "db-f1-micro"

  validation {
    condition     = contains(["db-f1-micro", "db-g1-small", "db-custom-1-3840"], var.db_tier)
    error_message = "DB tier must be one of: db-f1-micro, db-g1-small, db-custom-1-3840."
  }
}

variable "db_disk_size" {
  type        = number
  description = "Cloud SQL disk size in GB"
  default     = 10

  validation {
    condition     = var.db_disk_size >= 10 && var.db_disk_size <= 100
    error_message = "DB disk size must be between 10 and 100 GB."
  }
}

variable "db_deletion_protection" {
  type        = bool
  description = "Enable deletion protection for Cloud SQL instance"
  default     = false
}

# -----------------------------------------------------------------------------
# Cloud Run Configuration
# -----------------------------------------------------------------------------

variable "backend_cpu" {
  type        = string
  description = "CPU allocation for backend Cloud Run service"
  default     = "1"

  validation {
    condition     = contains(["1", "2", "4"], var.backend_cpu)
    error_message = "Backend CPU must be one of: 1, 2, 4."
  }
}

variable "backend_memory" {
  type        = string
  description = "Memory allocation for backend Cloud Run service"
  default     = "512Mi"

  validation {
    condition     = contains(["256Mi", "512Mi", "1Gi", "2Gi"], var.backend_memory)
    error_message = "Backend memory must be one of: 256Mi, 512Mi, 1Gi, 2Gi."
  }
}

variable "backend_min_instances" {
  type        = number
  description = "Minimum instances for backend (0 for cost optimization)"
  default     = 0

  validation {
    condition     = var.backend_min_instances >= 0 && var.backend_min_instances <= 10
    error_message = "Backend min instances must be between 0 and 10."
  }
}

variable "backend_max_instances" {
  type        = number
  description = "Maximum instances for backend"
  default     = 10

  validation {
    condition     = var.backend_max_instances >= 1 && var.backend_max_instances <= 100
    error_message = "Backend max instances must be between 1 and 100."
  }
}

variable "frontend_cpu" {
  type        = string
  description = "CPU allocation for frontend Cloud Run service"
  default     = "1"
}

variable "frontend_memory" {
  type        = string
  description = "Memory allocation for frontend Cloud Run service"
  default     = "256Mi"
}

variable "frontend_min_instances" {
  type        = number
  description = "Minimum instances for frontend (0 for cost optimization)"
  default     = 0
}

variable "frontend_max_instances" {
  type        = number
  description = "Maximum instances for frontend"
  default     = 5
}

# -----------------------------------------------------------------------------
# Container Images
# -----------------------------------------------------------------------------

variable "backend_image" {
  type        = string
  description = "Docker image for backend service (leave empty to use default)"
  default     = ""
}

variable "frontend_image" {
  type        = string
  description = "Docker image for frontend service (leave empty to use default)"
  default     = ""
}

# -----------------------------------------------------------------------------
# External Service API Keys (stored in Secret Manager)
# -----------------------------------------------------------------------------

variable "oauth_client_id" {
  type        = string
  description = "Google OAuth 2.0 Client ID"
  sensitive   = true
}

variable "oauth_client_secret" {
  type        = string
  description = "Google OAuth 2.0 Client Secret"
  sensitive   = true
}

variable "openai_api_key" {
  type        = string
  description = "OpenAI API Key"
  sensitive   = true
  default     = ""
}

variable "azure_speech_key" {
  type        = string
  description = "Azure Speech Services Key (optional)"
  sensitive   = true
  default     = ""
}

variable "azure_speech_region" {
  type        = string
  description = "Azure Speech Services Region (optional)"
  default     = ""
}

variable "google_tts_credentials" {
  type        = string
  description = "Google TTS Service Account JSON (optional, base64 encoded)"
  sensitive   = true
  default     = ""
}

variable "elevenlabs_api_key" {
  type        = string
  description = "ElevenLabs API Key (optional)"
  sensitive   = true
  default     = ""
}

# -----------------------------------------------------------------------------
# VPC Configuration
# -----------------------------------------------------------------------------

variable "vpc_connector_cidr" {
  type        = string
  description = "CIDR range for VPC Serverless Connector (must be /28)"
  default     = "10.8.0.0/28"

  validation {
    condition     = can(cidrhost(var.vpc_connector_cidr, 0)) && split("/", var.vpc_connector_cidr)[1] == "28"
    error_message = "VPC connector CIDR must be a valid /28 range."
  }
}

variable "vpc_connector_min_throughput" {
  type        = number
  description = "Minimum throughput for VPC connector (Mbps)"
  default     = 200
}

variable "vpc_connector_max_throughput" {
  type        = number
  description = "Maximum throughput for VPC connector (Mbps)"
  default     = 1000
}

# -----------------------------------------------------------------------------
# Terraform State Configuration
# -----------------------------------------------------------------------------

variable "tf_state_bucket" {
  type        = string
  description = "GCS bucket name for Terraform state (leave empty to auto-generate)"
  default     = ""
}

# -----------------------------------------------------------------------------
# Labels
# -----------------------------------------------------------------------------

variable "labels" {
  type        = map(string)
  description = "Labels to apply to all resources"
  default = {
    managed-by = "terraform"
    project    = "voice-lab"
  }
}
