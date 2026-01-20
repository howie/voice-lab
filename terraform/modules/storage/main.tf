# =============================================================================
# Storage Module - Cloud Storage Buckets
# =============================================================================

# Random suffix for bucket names (must be globally unique)
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Audio storage bucket
resource "google_storage_bucket" "audio" {
  name          = "voice-lab-audio-${var.project_id}-${random_id.bucket_suffix.hex}"
  project       = var.project_id
  location      = var.region
  storage_class = "STANDARD"

  # Allow destroy even if bucket contains objects (for test environments)
  force_destroy = var.force_destroy

  # Uniform bucket-level access (recommended)
  uniform_bucket_level_access = true

  # Lifecycle rules to manage costs
  lifecycle_rule {
    condition {
      age = 90 # Delete objects older than 90 days
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 30 # Move to nearline after 30 days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  # Versioning for data protection
  versioning {
    enabled = var.enable_versioning
  }

  # CORS configuration for frontend uploads
  cors {
    origin          = var.cors_origins
    method          = ["GET", "PUT", "POST", "DELETE"]
    response_header = ["Content-Type", "Content-Length", "Content-Range"]
    max_age_seconds = 3600
  }

  labels = var.labels
}

# Grant Cloud Run service account access to the audio bucket
resource "google_storage_bucket_iam_member" "audio_bucket_access" {
  bucket = google_storage_bucket.audio.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.service_account_email}"
}
