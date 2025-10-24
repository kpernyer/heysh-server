# Terraform outputs

output "backend_api_url" {
  description = "URL of the backend API (Cloud Run)"
  value       = google_cloud_run_service.backend_api.status[0].url
}

output "gke_cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.hey_sh_cluster.name
}

output "gke_cluster_endpoint" {
  description = "Endpoint for GKE cluster"
  value       = google_container_cluster.hey_sh_cluster.endpoint
  sensitive   = true
}

output "service_account_email" {
  description = "Email of the backend service account"
  value       = google_service_account.backend_sa.email
}
