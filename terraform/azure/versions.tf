# =============================================================================
# Azure Speech Services - Terraform Provider Configuration
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

# Configure the Azure provider
provider "azurerm" {
  features {}

  # Optional: specify subscription_id if you have multiple subscriptions
  # subscription_id = var.subscription_id
}
