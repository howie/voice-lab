# =============================================================================
# Networking Module Variables
# =============================================================================

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "region" {
  type        = string
  description = "GCP region"
}

variable "connector_cidr" {
  type        = string
  description = "CIDR range for VPC Serverless Connector (must be /28)"
  default     = "10.8.0.0/28"
}

variable "min_throughput" {
  type        = number
  description = "Minimum throughput for VPC connector (Mbps)"
  default     = 200
}

variable "max_throughput" {
  type        = number
  description = "Maximum throughput for VPC connector (Mbps)"
  default     = 1000
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply to resources"
  default     = {}
}
