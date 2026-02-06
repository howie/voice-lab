# =============================================================================
# Secrets Module Outputs
# =============================================================================

output "oauth_client_id_secret_id" {
  description = "Secret ID for OAuth Client ID"
  value       = google_secret_manager_secret.oauth_client_id.secret_id
}

output "oauth_client_secret_secret_id" {
  description = "Secret ID for OAuth Client Secret"
  value       = google_secret_manager_secret.oauth_client_secret.secret_id
}

output "openai_api_key_secret_id" {
  description = "Secret ID for OpenAI API Key"
  value       = var.openai_api_key != "" ? google_secret_manager_secret.openai_api_key[0].secret_id : null
}

output "azure_speech_key_secret_id" {
  description = "Secret ID for Azure Speech Key"
  value       = var.azure_speech_key != "" ? google_secret_manager_secret.azure_speech_key[0].secret_id : null
}

output "google_tts_credentials_secret_id" {
  description = "Secret ID for Google TTS Credentials"
  value       = var.google_tts_credentials != "" ? google_secret_manager_secret.google_tts_credentials[0].secret_id : null
}

output "elevenlabs_api_key_secret_id" {
  description = "Secret ID for ElevenLabs API Key"
  value       = var.elevenlabs_api_key != "" ? google_secret_manager_secret.elevenlabs_api_key[0].secret_id : null
}

output "gemini_api_key_secret_id" {
  description = "Secret ID for Gemini API Key"
  value       = var.gemini_api_key != "" ? google_secret_manager_secret.gemini_api_key[0].secret_id : null
}

output "voai_api_key_secret_id" {
  description = "Secret ID for VoAI API Key"
  value       = var.voai_api_key != "" ? google_secret_manager_secret.voai_api_key[0].secret_id : null
}

output "mureka_api_key_secret_id" {
  description = "Secret ID for Mureka AI API Key"
  value       = var.mureka_api_key != "" ? google_secret_manager_secret.mureka_api_key[0].secret_id : null
}
