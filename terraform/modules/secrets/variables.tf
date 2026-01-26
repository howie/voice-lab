# =============================================================================
# Secrets Module Variables
# =============================================================================

variable "project_id" {
  type        = string
  description = "GCP Project ID"
}

variable "service_account_email" {
  type        = string
  description = "Service account email to grant secret access"
}

# OAuth credentials
variable "oauth_client_id" {
  type        = string
  description = "Google OAuth Client ID"
  sensitive   = true
}

variable "oauth_client_secret" {
  type        = string
  description = "Google OAuth Client Secret"
  sensitive   = true
}

# API keys (optional)
variable "openai_api_key" {
  type        = string
  description = "OpenAI API Key"
  sensitive   = true
  default     = ""
}

variable "azure_speech_key" {
  type        = string
  description = "Azure Speech Services Key"
  sensitive   = true
  default     = ""
}

variable "google_tts_credentials" {
  type        = string
  description = "Google TTS Service Account JSON (base64 encoded)"
  sensitive   = true
  default     = ""
}

variable "elevenlabs_api_key" {
  type        = string
  description = "ElevenLabs API Key"
  sensitive   = true
  default     = ""
}

variable "gemini_api_key" {
  type        = string
  description = "Google Gemini API Key"
  sensitive   = true
  default     = ""
}

variable "labels" {
  type        = map(string)
  description = "Labels to apply to resources"
  default     = {}
}
