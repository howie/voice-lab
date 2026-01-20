# =============================================================================
# IAM Module Variables
# =============================================================================

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "create_build_service_account" {
  type        = bool
  description = "Whether to create a Cloud Build service account"
  default     = false
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply to resources"
  default     = {}
}
