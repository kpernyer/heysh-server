# Terraform variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "europe-west3"
}

variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "development"
}

variable "temporal_address" {
  description = "Temporal server address"
  type        = string
  default     = "europe-west3.gcp.api.temporal.io:7233" # Updated for Temporal Cloud
}

variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "kpernyer"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "heysh-server"
}

# Removed gke_node_count and gke_machine_type as they are not used by GKE Autopilot