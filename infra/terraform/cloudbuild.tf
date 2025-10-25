# Cloud Build configuration for CI/CD

# Enable Cloud Build API
resource "google_project_service" "cloudbuild_api" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Service account for Cloud Build
resource "google_service_account" "cloudbuild_sa" {
  account_id   = "${var.environment}-cloudbuild"
  display_name = "Cloud Build Service Account"
}

# Grant permissions to Cloud Build service account
resource "google_project_iam_member" "cloudbuild_sa_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/container.developer",
    "roles/iam.serviceAccountUser",
    "roles/secretmanager.secretAccessor",
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# Cloud Build trigger for backend API on main branch
resource "google_cloudbuild_trigger" "backend_main" {
  name        = "deploy-backend-main"
  description = "Deploy backend API to Cloud Run on push to main"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild_backend.yaml"

  service_account = google_service_account.cloudbuild_sa.id

  substitutions = {
    _REGION           = var.region
    _SERVICE_NAME     = "api"
    _DEPLOY_ENV       = var.environment
  }

  depends_on = [
    google_project_service.cloudbuild_api
  ]
}

# Cloud Build trigger for workers on main branch
resource "google_cloudbuild_trigger" "workers_main" {
  name        = "build-workers-main"
  description = "Build worker images on push to main"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild_workers.yaml"

  service_account = google_service_account.cloudbuild_sa.id

  substitutions = {
    _REGION           = var.region
    _DEPLOY_ENV       = var.environment
  }

  depends_on = [
    google_project_service.cloudbuild_api
  ]
}

# Cloud Build trigger for manual deployments (tags)
resource "google_cloudbuild_trigger" "deploy_tag" {
  name        = "deploy-tag"
  description = "Deploy on git tag (v*)"

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      tag = "^v.*"
    }
  }

  filename = "cloudbuild_deploy.yaml"

  service_account = google_service_account.cloudbuild_sa.id

  substitutions = {
    _REGION           = var.region
    _DEPLOY_ENV       = var.environment
  }

  depends_on = [
    google_project_service.cloudbuild_api
  ]
}
