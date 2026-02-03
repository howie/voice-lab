# =============================================================================
# Azure Speech Services - Outputs
# =============================================================================
# Note: API keys are intentionally NOT output here for security reasons.
# Use Azure CLI to retrieve keys: az cognitiveservices account keys list
# =============================================================================

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.speech.name
}

output "speech_service_name" {
  description = "Name of the Speech Service resource"
  value       = azurerm_cognitive_account.speech.name
}

output "speech_service_id" {
  description = "Resource ID of the Speech Service"
  value       = azurerm_cognitive_account.speech.id
}

output "speech_endpoint" {
  description = "Endpoint URL for the Speech Service"
  value       = azurerm_cognitive_account.speech.endpoint
}

output "speech_region" {
  description = "Azure region where the Speech Service is deployed"
  value       = azurerm_cognitive_account.speech.location
}

output "managed_identity_principal_id" {
  description = "Principal ID of the managed identity (if enabled)"
  value       = var.enable_managed_identity ? azurerm_cognitive_account.speech.identity[0].principal_id : null
}

output "managed_identity_tenant_id" {
  description = "Tenant ID of the managed identity (if enabled)"
  value       = var.enable_managed_identity ? azurerm_cognitive_account.speech.identity[0].tenant_id : null
}

# -----------------------------------------------------------------------------
# Helper: Azure CLI command to retrieve API keys
# -----------------------------------------------------------------------------
output "get_api_keys_command" {
  description = "Azure CLI command to retrieve API keys"
  value       = "az cognitiveservices account keys list --name ${azurerm_cognitive_account.speech.name} --resource-group ${azurerm_resource_group.speech.name}"
}

output "primary_access_key" {
  description = "Primary access key for the Speech Service (use for AZURE_SPEECH_KEY)"
  value       = azurerm_cognitive_account.speech.primary_access_key
  sensitive   = true
}

output "get_key1_command" {
  description = "Azure CLI command to retrieve only key1"
  value       = "az cognitiveservices account keys list --name ${azurerm_cognitive_account.speech.name} --resource-group ${azurerm_resource_group.speech.name} --query key1 -o tsv"
}
