# =============================================================================
# Artifact Registry Module Variables
# =============================================================================

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
}

variable "service_account_email" {
  type        = string
  description = "Service account email to grant pull access"
  default     = ""
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply to resources"
  default     = {}
}
