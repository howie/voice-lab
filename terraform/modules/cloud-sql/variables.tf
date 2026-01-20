# =============================================================================
# Cloud SQL Module Variables
# =============================================================================

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
}

variable "vpc_network_id" {
  type        = string
  description = "VPC network ID for private IP"
}

variable "tier" {
  type        = string
  description = "Cloud SQL instance tier"
  default     = "db-f1-micro"
}

variable "disk_size" {
  type        = number
  description = "Disk size in GB"
  default     = 10
}

variable "deletion_protection" {
  type        = bool
  description = "Enable deletion protection"
  default     = false
}

variable "high_availability" {
  type        = bool
  description = "Enable high availability (regional)"
  default     = false
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "test"
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply to resources"
  default     = {}
}
