terraform {
  required_version = ">= 1.5"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 6.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  apis = ["run.googleapis.com", "artifactregistry.googleapis.com", "storage.googleapis.com", "iam.googleapis.com"]
}

resource "google_project_service" "apis" {
  for_each           = toset(local.apis)
  service            = each.value
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.service_name
  format        = "DOCKER"
  depends_on    = [google_project_service.apis]
}

# Versioned model registry bucket
resource "google_storage_bucket" "models" {
  name                        = "${var.project_id}-${var.service_name}-models"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  versioning { enabled = true }
  lifecycle_rule {
    condition { num_newer_versions = 10 }
    action { type = "Delete" }
  }
}

# Runtime identity: can only READ models
resource "google_service_account" "runtime" {
  account_id   = "${var.service_name}-run"
  display_name = "Cloud Run runtime (read-only model access)"
}

resource "google_storage_bucket_iam_member" "runtime_read" {
  bucket = google_storage_bucket.models.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.runtime.email}"
}

resource "google_cloud_run_v2_service" "api" {
  name     = var.service_name
  location = var.region

  template {
    service_account = google_service_account.runtime.email
    scaling {
      min_instance_count = 0
      max_instance_count = var.max_instances
    }
    containers {
      image = var.image
      ports { container_port = 8080 }
      env {
        name  = "MODEL_GCS_URI"
        value = google_storage_bucket.models.url
      }
      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }
      startup_probe {
        http_get { path = "/health" }
        initial_delay_seconds = 5
        failure_threshold     = 10
      }
      liveness_probe {
        http_get { path = "/health" }
      }
    }
  }

  # CI manages revisions and traffic splits (canary) via gcloud after first apply
  lifecycle {
    ignore_changes = [template[0].containers[0].image, traffic, client, client_version]
  }
  depends_on = [google_project_service.apis]
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.allow_public ? 1 : 0
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
