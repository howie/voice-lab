# =============================================================================
# Azure Speech Services - Main Configuration
# =============================================================================
# This configuration creates Azure Cognitive Services Speech resource
# for TTS (Text-to-Speech) and STT (Speech-to-Text) functionality.
# =============================================================================

locals {
  common_tags = merge(var.tags, {
    Environment = var.environment
    ManagedBy   = "terraform"
    Service     = "voice-lab"
  })

  # Custom subdomain name (must be globally unique)
  custom_subdomain = var.enable_custom_subdomain ? var.speech_service_name : null
}

# -----------------------------------------------------------------------------
# Resource Group
# -----------------------------------------------------------------------------
resource "azurerm_resource_group" "speech" {
  name     = var.resource_group_name
  location = var.location
  tags     = local.common_tags
}

# -----------------------------------------------------------------------------
# Azure Cognitive Services - Speech Services
# -----------------------------------------------------------------------------
# This single resource provides both TTS and STT capabilities
# -----------------------------------------------------------------------------
resource "azurerm_cognitive_account" "speech" {
  name                = var.speech_service_name
  location            = azurerm_resource_group.speech.location
  resource_group_name = azurerm_resource_group.speech.name

  # SpeechServices kind provides both TTS and STT
  kind     = "SpeechServices"
  sku_name = var.sku_name

  # Custom subdomain (required for private endpoints and managed identity auth)
  custom_subdomain_name = local.custom_subdomain

  # Enable local authentication (API key based)
  # Set to false if using only managed identity authentication
  local_auth_enabled = true

  # System-assigned managed identity (optional, for Azure AD auth)
  dynamic "identity" {
    for_each = var.enable_managed_identity ? [1] : []
    content {
      type = "SystemAssigned"
    }
  }

  # Network access rules (optional)
  dynamic "network_acls" {
    for_each = length(var.allowed_ip_ranges) > 0 ? [1] : []
    content {
      default_action = "Deny"
      ip_rules       = var.allowed_ip_ranges
    }
  }

  tags = local.common_tags
}
