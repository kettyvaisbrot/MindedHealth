terraform {
  required_version = ">= 1.3"
  required_providers {
    aws = { source = "hashicorp/aws" }
    kubernetes = { source = "hashicorp/kubernetes" }
  }
}

provider "aws" {
  region = var.region
}
