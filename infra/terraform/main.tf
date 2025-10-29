# Main Terraform configuration for hey.sh backend infrastructure on GCP

terraform {
  required_version = ">= 1.5"

  backend "gcs" {
    bucket = "hey-sh-production-terraform-state"
    prefix = "terraform/state"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# A static map of secrets to grant access to. This avoids a dependency cycle.
locals {
  secrets_to_grant = {
    "SUPABASE_URL"         = google_secret_manager_secret.supabase_url,
    "SUPABASE_KEY"         = google_secret_manager_secret.supabase_key,
    "TEMPORAL_ADDRESS"     = google_secret_manager_secret.temporal_address,
    "TEMPORAL_NAMESPACE"   = google_secret_manager_secret.temporal_namespace,
    "TEMPORAL_API_KEY"     = google_secret_manager_secret.temporal_api_key,
    "TEMPORAL_TASK_QUEUE"  = google_secret_manager_secret.temporal_task_queue,
    "NEO4J_URI"            = google_secret_manager_secret.neo4j_uri,
    "NEO4J_USER"           = google_secret_manager_secret.neo4j_user,
    "NEO4J_PASSWORD"       = google_secret_manager_secret.neo4j_password,
    "WEAVIATE_URL"         = google_secret_manager_secret.weaviate_url,
    "WEAVIATE_API_KEY"     = google_secret_manager_secret.weaviate_api_key,
    "OPENAI_API_KEY"       = google_secret_manager_secret.openai_api_key,
    "ANTHROPIC_API_KEY"    = google_secret_manager_secret.anthropic_api_key,
    "GOOGLE_CLOUD_PROJECT" = google_secret_manager_secret.google_cloud_project,
  }
}

# GKE Autopilot Cluster for Workers
resource "google_container_cluster" "hey_sh_cluster" {
  name              = "${var.environment}-hey-sh-cluster"
  location          = var.region
  enable_autopilot  = true

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Enable vertical pod autoscaling for right-sizing (supported in Autopilot)
  vertical_pod_autoscaling {
    enabled = true
  }

  deletion_protection = var.environment == "production" ? true : false
}

# BigQuery dataset for cluster usage monitoring
resource "google_bigquery_dataset" "cluster_usage" {
  dataset_id = "cluster_usage_${var.environment}"
  location   = var.region

  delete_contents_on_destroy = var.environment != "production"
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "main_repo" {
  repository_id = "hey-sh-backend"
  location      = var.region
  format        = "DOCKER"
  description   = "Main Docker repository for hey-sh services"
}

# Cloud Run service for Backend API
resource "google_cloud_run_service" "backend_api" {
  name     = "api"
  location = var.region

  template {
    spec {
      service_account_name = google_service_account.backend_sa.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.main_repo.repository_id}/service:latest"

        ports {
          container_port = 8000
        }

        env {
          name  = "APP_ENV"
          value = var.environment
        }

        env {
          name = "SUPABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.supabase_url.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "SUPABASE_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.supabase_key.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "TEMPORAL_ADDRESS"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.temporal_address.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "TEMPORAL_NAMESPACE"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.temporal_namespace.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "TEMPORAL_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.temporal_api_key.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "TEMPORAL_TASK_QUEUE"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.temporal_task_queue.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "NEO4J_URI"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.neo4j_uri.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "NEO4J_USER"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.neo4j_user.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "NEO4J_PASSWORD"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.neo4j_password.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "WEAVIATE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.weaviate_url.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "WEAVIATE_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.weaviate_api_key.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "OPENAI_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.openai_api_key.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "ANTHROPIC_API_KEY"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.anthropic_api_key.secret_id
              key  = "latest"
            }
          }
        }
        env {
          name = "GOOGLE_CLOUD_PROJECT"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.google_cloud_project.secret_id
              key  = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "2000m"
            memory = "2Gi"
          }
        }
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = "0"
        "autoscaling.knative.dev/maxScale" = "10"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.run_api]
}

resource "google_cloud_run_service_iam_member" "public_access" {
  service  = google_cloud_run_service.backend_api.name
  location = google_cloud_run_service.backend_api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_service_account" "backend_sa" {
  account_id   = "${var.environment}-hey-sh-backend"
  display_name = "Hey.sh Backend Service Account"
}

# Correctly formatted secret resources
resource "google_secret_manager_secret" "supabase_url" {
  secret_id = "SUPABASE_URL"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "supabase_key" {
  secret_id = "SUPABASE_KEY"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "temporal_address" {
  secret_id = "TEMPORAL_ADDRESS"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "temporal_namespace" {
  secret_id = "TEMPORAL_NAMESPACE"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "temporal_api_key" {
  secret_id = "TEMPORAL_API_KEY"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "temporal_task_queue" {
  secret_id = "TEMPORAL_TASK_QUEUE"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "neo4j_uri" {
  secret_id = "NEO4J_URI"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "neo4j_user" {
  secret_id = "NEO4J_USER"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "neo4j_password" {
  secret_id = "NEO4J_PASSWORD"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "weaviate_url" {
  secret_id = "WEAVIATE_URL"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "weaviate_api_key" {
  secret_id = "WEAVIATE_API_KEY"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "OPENAI_API_KEY"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "anthropic_api_key" {
  secret_id = "ANTHROPIC_API_KEY"
  replication {
    auto {}
  }
}
resource "google_secret_manager_secret" "google_cloud_project" {
  secret_id = "GOOGLE_CLOUD_PROJECT"
  replication {
    auto {}
  }
}

# Grant secret access to the unified service account
resource "google_secret_manager_secret_iam_member" "backend_sa_secrets" {
  for_each = local.secrets_to_grant

  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.backend_sa.email}"
}

resource "google_project_service" "run_api" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "container_api" {
  service            = "container.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "secretmanager_api" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "artifactregistry_api" {
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}
resource "google_project_service" "bigquery_api" {
  service            = "bigquery.googleapis.com"
  disable_on_destroy = false
}
