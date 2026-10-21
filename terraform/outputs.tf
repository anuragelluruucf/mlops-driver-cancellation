output "service_url" { value = google_cloud_run_v2_service.api.uri }
output "model_bucket" { value = google_storage_bucket.models.url }
output "registry_repo" { value = google_artifact_registry_repository.repo.id }
output "runtime_sa" { value = google_service_account.runtime.email }
