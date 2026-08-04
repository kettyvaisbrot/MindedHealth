variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1" # N. Virginia
}

variable "project_name" {
  description = "Prefix for resource names"
  type        = string
  default     = "mindedhealth"
}

variable "db_username" {
  description = "RDS PostgreSQL username"
  type        = string
}

variable "db_password" {
  description = "RDS PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "mindedhealth"
}

variable "app_instance_type" {
  description = "Instance type for the single app server (runs all services via Docker Compose)"
  type        = string
  default     = "t3.micro"
}
