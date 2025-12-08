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

variable "eks_cluster_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.30"
}

variable "eks_node_instance_type" {
  description = "Instance type for EKS nodes"
  type        = string
  default     = "t3.medium"
}

variable "eks_desired_capacity" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}
