terraform {
  required_version = ">= 1.5.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

# Credentials are read from the environment (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY),
# exported via .envrc — no static credentials in Terraform files.
provider "aws" {
  region = var.aws_region
}
