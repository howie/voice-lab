# =============================================================================
# Azure Speech Services - Variables
# =============================================================================

variable "resource_group_name" {
  description = "Name of the Azure resource group"
  type        = string
  default     = "voice-lab-speech-rg"
}

variable "location" {
  description = "Azure region for resources (use region close to your users)"
  type        = string
  default     = "eastasia"

  validation {
    condition = contains([
      "eastasia",
      "southeastasia",
      "japaneast",
      "japanwest",
      "koreacentral",
      "eastus",
      "eastus2",
      "westus",
      "westus2",
      "westeurope",
      "northeurope"
    ], var.location)
    error_message = "Location must be a valid Azure region that supports Speech Services."
  }
}

variable "speech_service_name" {
  description = "Name of the Azure Speech Service resource"
  type        = string
  default     = "voice-lab-speech"
}

variable "sku_name" {
  description = "SKU for Speech Service: F0 (free, dev/test) or S0 (standard, production)"
  type        = string
  default     = "S0"

  validation {
    condition     = contains(["F0", "S0"], var.sku_name)
    error_message = "SKU must be either F0 (free) or S0 (standard)."
  }
}

variable "enable_custom_subdomain" {
  description = "Enable custom subdomain (required for private endpoints and Entra ID auth)"
  type        = bool
  default     = true
}

variable "enable_managed_identity" {
  description = "Enable system-assigned managed identity"
  type        = bool
  default     = true
}

variable "allowed_ip_ranges" {
  description = "List of IP addresses/CIDR ranges allowed to access the service (empty = allow all)"
  type        = list(string)
  default     = []
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
