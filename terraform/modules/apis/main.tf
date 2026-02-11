# =============================================================================
# APIs Module - Enable Required GCP APIs
# =============================================================================

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",                    # Cloud Run
    "sqladmin.googleapis.com",               # Cloud SQL Admin
    "sql-component.googleapis.com",          # Cloud SQL
    "secretmanager.googleapis.com",          # Secret Manager
    "compute.googleapis.com",                # Compute Engine (for VPC)
    "vpcaccess.googleapis.com",              # VPC Access Connector
    "servicenetworking.googleapis.com",      # Service Networking
    "artifactregistry.googleapis.com",       # Artifact Registry
    "cloudbuild.googleapis.com",             # Cloud Build
    "iam.googleapis.com",                    # IAM
    "iamcredentials.googleapis.com",         # IAM Credentials
    "texttospeech.googleapis.com",           # Cloud Text-to-Speech
    "cloudscheduler.googleapis.com",         # Cloud Scheduler (keep-warm)
  ])

  project = var.project_id
  service = each.value

  # Don't disable the API on destroy (safer for shared projects)
  disable_on_destroy = false

  # Wait for the API to be fully enabled before proceeding
  timeouts {
    create = "10m"
    update = "10m"
  }
}

# Wait for all APIs to be enabled
resource "time_sleep" "api_propagation" {
  depends_on      = [google_project_service.apis]
  create_duration = "30s"
}
