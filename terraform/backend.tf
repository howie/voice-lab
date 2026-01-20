# =============================================================================
# Voice Lab GCP Terraform Backend Configuration
# =============================================================================
# GCS backend with native state locking (Terraform 1.10+)
#
# Usage:
#   terraform init \
#     -backend-config="bucket=voice-lab-tf-state-YOUR_PROJECT_ID" \
#     -backend-config="prefix=terraform/state"
# =============================================================================

terraform {
  backend "gcs" {
    # These values should be provided via -backend-config during terraform init
    # bucket = "voice-lab-tf-state-YOUR_PROJECT_ID"
    # prefix = "terraform/state"
  }
}
