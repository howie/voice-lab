# =============================================================================
# Storage Module Outputs
# =============================================================================

output "audio_bucket_name" {
  description = "Name of the audio storage bucket"
  value       = google_storage_bucket.audio.name
}

output "audio_bucket_url" {
  description = "URL of the audio storage bucket"
  value       = google_storage_bucket.audio.url
}

output "audio_bucket_self_link" {
  description = "Self link of the audio storage bucket"
  value       = google_storage_bucket.audio.self_link
}
