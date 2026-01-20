# =============================================================================
# Secrets Module - Secret Manager for Sensitive Data
# =============================================================================

# -----------------------------------------------------------------------------
# OAuth Secrets
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "oauth_client_id" {
  secret_id = "voice-lab-oauth-client-id"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "oauth_client_id" {
  secret      = google_secret_manager_secret.oauth_client_id.id
  secret_data = var.oauth_client_id
}

resource "google_secret_manager_secret" "oauth_client_secret" {
  secret_id = "voice-lab-oauth-client-secret"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "oauth_client_secret" {
  secret      = google_secret_manager_secret.oauth_client_secret.id
  secret_data = var.oauth_client_secret
}

# -----------------------------------------------------------------------------
# API Keys (optional)
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret" "openai_api_key" {
  count = var.openai_api_key != "" ? 1 : 0

  secret_id = "voice-lab-openai-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "openai_api_key" {
  count = var.openai_api_key != "" ? 1 : 0

  secret      = google_secret_manager_secret.openai_api_key[0].id
  secret_data = var.openai_api_key
}

resource "google_secret_manager_secret" "azure_speech_key" {
  count = var.azure_speech_key != "" ? 1 : 0

  secret_id = "voice-lab-azure-speech-key"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "azure_speech_key" {
  count = var.azure_speech_key != "" ? 1 : 0

  secret      = google_secret_manager_secret.azure_speech_key[0].id
  secret_data = var.azure_speech_key
}

resource "google_secret_manager_secret" "google_tts_credentials" {
  count = var.google_tts_credentials != "" ? 1 : 0

  secret_id = "voice-lab-google-tts-credentials"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "google_tts_credentials" {
  count = var.google_tts_credentials != "" ? 1 : 0

  secret      = google_secret_manager_secret.google_tts_credentials[0].id
  secret_data = var.google_tts_credentials
}

resource "google_secret_manager_secret" "elevenlabs_api_key" {
  count = var.elevenlabs_api_key != "" ? 1 : 0

  secret_id = "voice-lab-elevenlabs-api-key"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "elevenlabs_api_key" {
  count = var.elevenlabs_api_key != "" ? 1 : 0

  secret      = google_secret_manager_secret.elevenlabs_api_key[0].id
  secret_data = var.elevenlabs_api_key
}

# -----------------------------------------------------------------------------
# IAM - Grant service account access to secrets
# -----------------------------------------------------------------------------

resource "google_secret_manager_secret_iam_member" "oauth_client_id_access" {
  secret_id = google_secret_manager_secret.oauth_client_id.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "oauth_client_secret_access" {
  secret_id = google_secret_manager_secret.oauth_client_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "openai_api_key_access" {
  count = var.openai_api_key != "" ? 1 : 0

  secret_id = google_secret_manager_secret.openai_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "azure_speech_key_access" {
  count = var.azure_speech_key != "" ? 1 : 0

  secret_id = google_secret_manager_secret.azure_speech_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "google_tts_credentials_access" {
  count = var.google_tts_credentials != "" ? 1 : 0

  secret_id = google_secret_manager_secret.google_tts_credentials[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret_iam_member" "elevenlabs_api_key_access" {
  count = var.elevenlabs_api_key != "" ? 1 : 0

  secret_id = google_secret_manager_secret.elevenlabs_api_key[0].id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}
