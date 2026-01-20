# =============================================================================
# Storage Module Variables
# =============================================================================

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP region for bucket location"
}

variable "service_account_email" {
  type        = string
  description = "Service account email to grant bucket access"
}

variable "force_destroy" {
  type        = bool
  description = "Allow bucket to be destroyed even if it contains objects"
  default     = true
}

variable "enable_versioning" {
  type        = bool
  description = "Enable object versioning"
  default     = false
}

variable "cors_origins" {
  type        = list(string)
  description = "CORS allowed origins"
  default     = ["*"]
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply to resources"
  default     = {}
}
