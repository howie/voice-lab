# =============================================================================
# Voice Lab GCP Terraform Main Configuration
# =============================================================================
# This file orchestrates all modules for the Voice Lab GCP deployment.
# =============================================================================

# Merge labels with environment
locals {
  common_labels = merge(var.labels, {
    environment = var.environment
  })

  # Determine container images
  backend_image = var.backend_image != "" ? var.backend_image : "${var.region}-docker.pkg.dev/${var.project_id}/voice-lab/backend:latest"
  frontend_image = var.frontend_image != "" ? var.frontend_image : "${var.region}-docker.pkg.dev/${var.project_id}/voice-lab/frontend:latest"

  # Determine custom domain URLs
  backend_url  = var.custom_domain != "" ? "https://${var.api_subdomain}.${var.custom_domain}" : module.cloud_run.backend_url
  frontend_url = var.custom_domain != "" ? "https://${var.custom_domain}" : module.cloud_run.frontend_url
}

# -----------------------------------------------------------------------------
# Module: APIs - Enable required GCP APIs
# -----------------------------------------------------------------------------
module "apis" {
  source = "./modules/apis"

  project_id = var.project_id
}

# -----------------------------------------------------------------------------
# Module: IAM - Service accounts and permissions
# -----------------------------------------------------------------------------
module "iam" {
  source = "./modules/iam"

  project_id = var.project_id
  labels     = local.common_labels

  depends_on = [module.apis]
}

# -----------------------------------------------------------------------------
# Module: Networking - VPC and Serverless Connector
# -----------------------------------------------------------------------------
module "networking" {
  source = "./modules/networking"

  project_id     = var.project_id
  region         = var.region
  connector_cidr = var.vpc_connector_cidr
  min_throughput = var.vpc_connector_min_throughput
  max_throughput = var.vpc_connector_max_throughput
  labels         = local.common_labels

  depends_on = [module.apis]
}

# -----------------------------------------------------------------------------
# Module: Storage - Cloud Storage buckets
# -----------------------------------------------------------------------------
module "storage" {
  source = "./modules/storage"

  project_id            = var.project_id
  region                = var.region
  service_account_email = module.iam.cloud_run_service_account_email
  force_destroy         = var.environment != "prod"
  labels                = local.common_labels

  depends_on = [module.iam]
}

# -----------------------------------------------------------------------------
# Module: Artifact Registry - Container image repository
# -----------------------------------------------------------------------------
module "artifact_registry" {
  source = "./modules/artifact-registry"

  project_id = var.project_id
  region     = var.region
  labels     = local.common_labels

  depends_on = [module.apis]
}

# -----------------------------------------------------------------------------
# Module: Secrets - Secret Manager for sensitive data
# -----------------------------------------------------------------------------
module "secrets" {
  source = "./modules/secrets"

  project_id            = var.project_id
  service_account_email = module.iam.cloud_run_service_account_email

  oauth_client_id        = var.oauth_client_id
  oauth_client_secret    = var.oauth_client_secret
  openai_api_key         = var.openai_api_key
  azure_speech_key       = var.azure_speech_key
  google_tts_credentials = var.google_tts_credentials
  elevenlabs_api_key     = var.elevenlabs_api_key
  gemini_api_key         = var.gemini_api_key
  voai_api_key           = var.voai_api_key

  labels = local.common_labels

  depends_on = [module.apis, module.iam]
}

# -----------------------------------------------------------------------------
# Module: Cloud SQL - PostgreSQL database
# -----------------------------------------------------------------------------
module "cloud_sql" {
  source = "./modules/cloud-sql"

  project_id          = var.project_id
  region              = var.region
  vpc_network_id      = module.networking.vpc_id
  tier                = var.db_tier
  disk_size           = var.db_disk_size
  deletion_protection = var.db_deletion_protection
  labels              = local.common_labels

  depends_on = [module.networking]
}

# -----------------------------------------------------------------------------
# Module: Cloud Run - Backend and Frontend services
# -----------------------------------------------------------------------------
module "cloud_run" {
  source = "./modules/cloud-run"

  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  service_account_email = module.iam.cloud_run_service_account_email
  vpc_connector_id      = module.networking.connector_id

  # Backend configuration
  backend_image         = local.backend_image
  backend_cpu           = var.backend_cpu
  backend_memory        = var.backend_memory
  backend_min_instances = var.backend_min_instances
  backend_max_instances = var.backend_max_instances

  # Frontend configuration
  frontend_image         = local.frontend_image
  frontend_cpu           = var.frontend_cpu
  frontend_memory        = var.frontend_memory
  frontend_min_instances = var.frontend_min_instances
  frontend_max_instances = var.frontend_max_instances

  # Database connection
  database_connection_name = module.cloud_sql.connection_name
  database_host            = module.cloud_sql.private_ip
  database_name            = module.cloud_sql.database_name
  database_user            = module.cloud_sql.database_user
  database_password_secret = module.cloud_sql.database_password_secret_id

  # Secrets
  oauth_client_id_secret     = module.secrets.oauth_client_id_secret_id
  oauth_client_secret_secret = module.secrets.oauth_client_secret_secret_id
  openai_api_key_secret      = module.secrets.openai_api_key_secret_id
  gemini_api_key_secret      = module.secrets.gemini_api_key_secret_id
  voai_api_key_secret        = module.secrets.voai_api_key_secret_id
  voai_api_endpoint          = var.voai_api_endpoint
  azure_speech_key_secret    = module.secrets.azure_speech_key_secret_id
  azure_speech_region        = var.azure_speech_region
  elevenlabs_api_key_secret  = module.secrets.elevenlabs_api_key_secret_id

  # Application config
  allowed_domains         = var.allowed_domains
  audio_bucket            = module.storage.audio_bucket_name
  custom_domain           = var.custom_domain
  api_subdomain           = var.api_subdomain
  additional_cors_origins = var.additional_cors_origins

  labels = local.common_labels

  depends_on = [
    module.iam,
    module.networking,
    module.secrets,
    module.cloud_sql,
    module.storage,
    module.artifact_registry
  ]
}

# -----------------------------------------------------------------------------
# Cloudflare DNS (optional - only if cloudflare_api_token is provided)
# -----------------------------------------------------------------------------
resource "cloudflare_record" "frontend" {
  count = var.cloudflare_api_token != "" && var.custom_domain != "" ? 1 : 0

  zone_id = var.cloudflare_zone_id
  name    = var.frontend_subdomain
  content = "ghs.googlehosted.com"
  type    = "CNAME"
  ttl     = 1     # Auto
  proxied = false # DNS only (required for Cloud Run domain mapping)

  comment = "Voice Lab frontend - managed by Terraform"
}

resource "cloudflare_record" "backend" {
  count = var.cloudflare_api_token != "" && var.custom_domain != "" ? 1 : 0

  zone_id = var.cloudflare_zone_id
  name    = "${var.api_subdomain}.${var.frontend_subdomain}"
  content = "ghs.googlehosted.com"
  type    = "CNAME"
  ttl     = 1     # Auto
  proxied = false # DNS only (required for Cloud Run domain mapping)

  comment = "Voice Lab API - managed by Terraform"
}
