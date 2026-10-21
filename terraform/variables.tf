variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "us-central1"
}
variable "service_name" {
  type    = string
  default = "driver-cancel-risk"
}
variable "image" {
  type        = string
  description = "Initial image, e.g. us-central1-docker.pkg.dev/PROJECT/driver-cancel-risk/api:SHA"
}
variable "max_instances" {
  type    = number
  default = 3
}
variable "allow_public" {
  type    = bool
  default = false
}
