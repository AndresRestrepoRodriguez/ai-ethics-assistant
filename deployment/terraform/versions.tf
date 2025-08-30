# versions.tf - Terraform Version and Provider Requirements
# This file specifies which versions of Terraform and providers we need
# Think of it like requirements.txt in Python or package.json in Node.js

terraform {
  # Minimum Terraform version required
  # We use >= 1.0 to ensure we have all modern features
  required_version = ">= 1.0"
  
  # Providers are plugins that Terraform uses to manage resources
  # Each cloud provider (AWS, Azure, GCP) has its own provider
  required_providers {
    aws = {
      source  = "hashicorp/aws"  # Official AWS provider from HashiCorp
      version = "~> 5.0"          # Use version 5.x (won't auto-upgrade to 6.0)
    }
  }
}

# Why version constraints matter:
# - ">= 1.0" means any version 1.0 or higher
# - "~> 5.0" means >= 5.0 but < 6.0 (stay within major version)
# This prevents breaking changes from affecting our infrastructure