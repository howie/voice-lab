# =============================================================================
# IAM Module - Service Accounts and Permissions
# =============================================================================

# Cloud Run Service Account
resource "google_service_account" "cloud_run" {
  account_id   = "voice-lab-cloud-run"
  display_name = "Voice Lab Cloud Run Service Account"
  description  = "Service account for Voice Lab Cloud Run services"
  project      = var.project_id
}

# Grant Cloud Run service account necessary roles
resource "google_project_iam_member" "cloud_run_roles" {
  for_each = toset([
    "roles/cloudsql.client",           # Connect to Cloud SQL
    "roles/secretmanager.secretAccessor", # Access secrets
    "roles/storage.objectViewer",      # Read from Cloud Storage
    "roles/storage.objectCreator",     # Write to Cloud Storage
    "roles/logging.logWriter",         # Write logs
    "roles/cloudtrace.agent",          # Cloud Trace
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Service account for Cloud Build (optional, for CI/CD)
resource "google_service_account" "cloud_build" {
  count = var.create_build_service_account ? 1 : 0

  account_id   = "voice-lab-cloud-build"
  display_name = "Voice Lab Cloud Build Service Account"
  description  = "Service account for Voice Lab Cloud Build"
  project      = var.project_id
}

# Grant Cloud Build service account necessary roles
resource "google_project_iam_member" "cloud_build_roles" {
  for_each = var.create_build_service_account ? toset([
    "roles/cloudbuild.builds.builder",
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
  ]) : toset([])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.cloud_build[0].email}"
}
