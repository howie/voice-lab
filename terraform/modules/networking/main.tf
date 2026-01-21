# =============================================================================
# Networking Module - VPC and Serverless Connector
# =============================================================================

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = "voice-lab-vpc"
  project                 = var.project_id
  auto_create_subnetworks = false
  description             = "VPC network for Voice Lab"
}

# Subnet for VPC Connector
resource "google_compute_subnetwork" "connector_subnet" {
  name          = "voice-lab-connector-subnet"
  project       = var.project_id
  region        = var.region
  network       = google_compute_network.vpc.id
  ip_cidr_range = var.connector_cidr

  private_ip_google_access = true
}

# Private IP range for Cloud SQL
resource "google_compute_global_address" "private_ip_range" {
  name          = "voice-lab-private-ip"
  project       = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

# Private connection for Cloud SQL
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]

  deletion_policy = "ABANDON"
}

# VPC Serverless Connector for Cloud Run to access Cloud SQL
resource "google_vpc_access_connector" "connector" {
  name    = "voice-lab-connector"
  project = var.project_id
  region  = var.region

  # Use existing subnet instead of network + ip_cidr_range to avoid conflicts
  subnet {
    name       = google_compute_subnetwork.connector_subnet.name
    project_id = var.project_id
  }

  min_throughput = var.min_throughput
  max_throughput = var.max_throughput
}

# Firewall rule to allow internal traffic
resource "google_compute_firewall" "allow_internal" {
  name    = "voice-lab-allow-internal"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
  description   = "Allow internal traffic within VPC"
}
