# =============================================================================
# Cloud Run Module - Backend and Frontend Services
# =============================================================================

# -----------------------------------------------------------------------------
# Backend Service
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "backend" {
  name     = "voice-lab-backend"
  project  = var.project_id
  location = var.region

  # Allow unauthenticated access (auth handled by application)
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.backend_min_instances
      max_instance_count = var.backend_max_instances
    }

    # VPC access for Cloud SQL
    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = var.backend_image

      resources {
        limits = {
          cpu    = var.backend_cpu
          memory = var.backend_memory
        }
        cpu_idle = true # Cost optimization: CPU only allocated during requests
      }

      # Environment variables
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      # NLTK data directory (pre-downloaded in Docker image)
      env {
        name  = "NLTK_DATA"
        value = "/app/nltk_data"
      }

      env {
        name  = "DATABASE_HOST"
        value = var.database_host
      }

      env {
        name  = "DATABASE_NAME"
        value = var.database_name
      }

      env {
        name  = "DATABASE_USER"
        value = var.database_user
      }

      env {
        name  = "ALLOWED_DOMAINS"
        value = join(",", var.allowed_domains)
      }

      env {
        name  = "AUDIO_BUCKET"
        value = var.audio_bucket
      }

      env {
        name  = "FRONTEND_URL"
        value = var.custom_domain != "" ? "https://${var.custom_domain}" : ""
      }

      # Backend base URL for OAuth callback
      env {
        name  = "BASE_URL"
        value = var.custom_domain != "" ? "https://${var.api_subdomain}.${var.custom_domain}" : ""
      }

      # CORS origins - custom domain, additional origins, and localhost for development
      env {
        name  = "CORS_ORIGINS"
        value = join(",", concat(
          var.custom_domain != "" ? ["https://${var.custom_domain}"] : [],
          var.additional_cors_origins,
          ["http://localhost:5173", "http://localhost:3000"]
        ))
      }

      # Database password from Secret Manager
      env {
        name = "DATABASE_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = var.database_password_secret
            version = "latest"
          }
        }
      }

      # OAuth secrets from Secret Manager
      env {
        name = "GOOGLE_OAUTH_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = var.oauth_client_id_secret
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_OAUTH_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = var.oauth_client_secret_secret
            version = "latest"
          }
        }
      }

      # OpenAI API key (if provided)
      dynamic "env" {
        for_each = var.openai_api_key_secret != null ? [1] : []
        content {
          name = "OPENAI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = var.openai_api_key_secret
              version = "latest"
            }
          }
        }
      }

      # Gemini API key (if provided)
      dynamic "env" {
        for_each = var.gemini_api_key_secret != null ? [1] : []
        content {
          name = "GEMINI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = var.gemini_api_key_secret
              version = "latest"
            }
          }
        }
      }

      # VoAI API key (if provided)
      dynamic "env" {
        for_each = var.voai_api_key_secret != null ? [1] : []
        content {
          name = "VOAI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = var.voai_api_key_secret
              version = "latest"
            }
          }
        }
      }

      # VoAI API endpoint
      env {
        name  = "VOAI_API_ENDPOINT"
        value = var.voai_api_endpoint
      }

      # Azure Speech key (if provided)
      dynamic "env" {
        for_each = var.azure_speech_key_secret != null ? [1] : []
        content {
          name = "AZURE_SPEECH_KEY"
          value_source {
            secret_key_ref {
              secret  = var.azure_speech_key_secret
              version = "latest"
            }
          }
        }
      }

      # Azure Speech region
      dynamic "env" {
        for_each = var.azure_speech_key_secret != null ? [1] : []
        content {
          name  = "AZURE_SPEECH_REGION"
          value = var.azure_speech_region
        }
      }

      # ElevenLabs API key (if provided)
      dynamic "env" {
        for_each = var.elevenlabs_api_key_secret != null ? [1] : []
        content {
          name = "ELEVENLABS_API_KEY"
          value_source {
            secret_key_ref {
              secret  = var.elevenlabs_api_key_secret
              version = "latest"
            }
          }
        }
      }

      # Startup and liveness probes
      startup_probe {
        http_get {
          path = "/api/v1/health"
          port = 8000
        }
        initial_delay_seconds = 10
        period_seconds        = 10
        timeout_seconds       = 5
        failure_threshold     = 6
      }

      liveness_probe {
        http_get {
          path = "/api/v1/health"
          port = 8000
        }
        period_seconds    = 30
        failure_threshold = 3
      }

      ports {
        container_port = 8000
      }
    }

    labels = var.labels
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  lifecycle {
    ignore_changes = [
      client,
      client_version,
    ]
  }
}

# Allow public access to backend
resource "google_cloud_run_v2_service_iam_member" "backend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Backend domain mapping (if custom domain provided)
resource "google_cloud_run_domain_mapping" "backend" {
  count = var.custom_domain != "" ? 1 : 0

  name     = "${var.api_subdomain}.${var.custom_domain}"
  project  = var.project_id
  location = var.region

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.backend.name
  }

  lifecycle {
    ignore_changes = [metadata[0].annotations]
  }
}

# -----------------------------------------------------------------------------
# Frontend Service
# -----------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "frontend" {
  name     = "voice-lab-frontend"
  project  = var.project_id
  location = var.region

  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.frontend_min_instances
      max_instance_count = var.frontend_max_instances
    }

    containers {
      image = var.frontend_image

      resources {
        limits = {
          cpu    = var.frontend_cpu
          memory = var.frontend_memory
        }
        cpu_idle = true
      }

      # Environment variables for runtime config
      env {
        name  = "VITE_API_URL"
        value = var.custom_domain != "" ? "https://${var.api_subdomain}.${var.custom_domain}" : google_cloud_run_v2_service.backend.uri
      }

      env {
        name  = "VITE_WS_URL"
        value = var.custom_domain != "" ? "wss://${var.api_subdomain}.${var.custom_domain}" : replace(google_cloud_run_v2_service.backend.uri, "https://", "wss://")
      }

      env {
        name = "VITE_GOOGLE_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = var.oauth_client_id_secret
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 2
        period_seconds        = 5
        failure_threshold     = 3
      }

      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        period_seconds    = 30
        failure_threshold = 3
      }

      ports {
        container_port = 8080
      }
    }

    labels = var.labels
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  lifecycle {
    ignore_changes = [
      client,
      client_version,
    ]
  }
}

# Allow public access to frontend
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Frontend domain mapping (if custom domain provided)
resource "google_cloud_run_domain_mapping" "frontend" {
  count = var.custom_domain != "" ? 1 : 0

  name     = var.custom_domain
  project  = var.project_id
  location = var.region

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.frontend.name
  }

  lifecycle {
    ignore_changes = [metadata[0].annotations]
  }
}
