# =============================================================================
# Cloud SQL Module - PostgreSQL Database
# =============================================================================

# Random password for database
resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Store database password in Secret Manager
resource "google_secret_manager_secret" "db_password" {
  secret_id = "voice-lab-db-password"
  project   = var.project_id

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}

# Cloud SQL PostgreSQL Instance
resource "google_sql_database_instance" "main" {
  name             = "voice-lab-postgres"
  project          = var.project_id
  region           = var.region
  database_version = "POSTGRES_16"

  # Allow deletion for test environments
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    disk_size         = var.disk_size
    disk_type         = "PD_SSD"
    disk_autoresize   = true
    availability_type = var.high_availability ? "REGIONAL" : "ZONAL"

    # IP configuration - private only
    ip_configuration {
      ipv4_enabled                                  = false
      private_network                               = var.vpc_network_id
      enable_private_path_for_google_cloud_services = true
    }

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod"
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    # Maintenance window
    maintenance_window {
      day          = 7 # Sunday
      hour         = 4 # 4 AM
      update_track = "stable"
    }

    # Database flags
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    user_labels = var.labels
  }

  lifecycle {
    prevent_destroy = false
  }
}

# Database
resource "google_sql_database" "main" {
  name     = "voicelab"
  project  = var.project_id
  instance = google_sql_database_instance.main.name
}

# Database user
resource "google_sql_user" "main" {
  name     = "voicelab"
  project  = var.project_id
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}
