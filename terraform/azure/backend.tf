# =============================================================================
# Azure Speech Services - Remote State Backend Configuration
# =============================================================================
# Uses Azure Storage as the Terraform state backend.
#
# Prerequisites:
#   1. Create a Resource Group for state storage:
#      az group create --name voice-lab-tfstate-rg --location eastasia
#
#   2. Create a Storage Account:
#      az storage account create --name voicelabtfstate \
#        --resource-group voice-lab-tfstate-rg \
#        --location eastasia --sku Standard_LRS
#
#   3. Create a Blob Container:
#      az storage container create --name tfstate \
#        --account-name voicelabtfstate
#
# Usage:
#   terraform init \
#     -backend-config="resource_group_name=voice-lab-tfstate-rg" \
#     -backend-config="storage_account_name=voicelabtfstate" \
#     -backend-config="container_name=tfstate" \
#     -backend-config="key=azure-speech.tfstate"
#
#   Or create a backend.hcl file and use: terraform init -backend-config=backend.hcl
# =============================================================================

terraform {
  backend "azurerm" {
    # Configured via -backend-config or backend.hcl
    # resource_group_name  = "voice-lab-tfstate-rg"
    # storage_account_name = "voicelabtfstate"
    # container_name       = "tfstate"
    # key                  = "azure-speech.tfstate"
  }
}
