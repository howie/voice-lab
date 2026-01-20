# =============================================================================
# Networking Module Outputs
# =============================================================================

output "vpc_id" {
  description = "ID of the VPC network"
  value       = google_compute_network.vpc.id
}

output "vpc_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.vpc.name
}

output "vpc_self_link" {
  description = "Self link of the VPC network"
  value       = google_compute_network.vpc.self_link
}

output "connector_id" {
  description = "ID of the VPC Access Connector"
  value       = google_vpc_access_connector.connector.id
}

output "connector_name" {
  description = "Name of the VPC Access Connector"
  value       = google_vpc_access_connector.connector.name
}

output "private_vpc_connection" {
  description = "Private VPC connection for Cloud SQL"
  value       = google_service_networking_connection.private_vpc_connection.id
}
