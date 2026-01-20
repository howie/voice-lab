# =============================================================================
# Cloud SQL Module Outputs
# =============================================================================

output "connection_name" {
  description = "Cloud SQL instance connection name"
  value       = google_sql_database_instance.main.connection_name
}

output "private_ip" {
  description = "Private IP address of Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.main.name
}

output "database_name" {
  description = "Name of the database"
  value       = google_sql_database.main.name
}

output "database_user" {
  description = "Database username"
  value       = google_sql_user.main.name
}

output "database_password_secret_id" {
  description = "Secret ID for database password"
  value       = google_secret_manager_secret.db_password.secret_id
}
