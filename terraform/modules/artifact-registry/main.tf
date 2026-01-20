# =============================================================================
# Artifact Registry Module - Container Image Repository
# =============================================================================

resource "google_artifact_registry_repository" "main" {
  repository_id = "voice-lab"
  project       = var.project_id
  location      = var.region
  format        = "DOCKER"
  description   = "Docker repository for Voice Lab container images"

  # Cleanup policy for old images
  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-minimum-versions"
    action = "KEEP"

    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "delete-old-images"
    action = "DELETE"

    condition {
      older_than = "2592000s" # 30 days
    }
  }

  labels = var.labels
}

# Grant Cloud Run service account pull access
resource "google_artifact_registry_repository_iam_member" "cloud_run_reader" {
  count = var.service_account_email != "" ? 1 : 0

  project    = var.project_id
  location   = var.region
  repository = google_artifact_registry_repository.main.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${var.service_account_email}"
}
