# main.tf - AWS Provider Configuration
# This file tells Terraform how to connect to AWS and which account to use

# Configure the AWS Provider
provider "aws" {
  # AWS Region where resources will be created
  # us-east-1 is Northern Virginia, often cheapest and most feature-complete
  region  = var.aws_region
  
  # AWS Profile to use (from ~/.aws/credentials)
  # This uses your terraform-rag profile we set up earlier
  profile = "terraform-rag"
}

# Data source to get current AWS account information
# This is useful for verification and for building ARNs
data "aws_caller_identity" "current" {}

# Data source to get current region
data "aws_region" "current" {}

# Local values that can be reused throughout the configuration
locals {
  # Common tags to apply to all resources
  # Tags help with organization, billing tracking, and resource management
  common_tags = {
    Project     = var.project_name
    Environment = "production"
    ManagedBy   = "terraform"
    Owner       = data.aws_caller_identity.current.user_id
    CreatedAt   = timestamp()
  }
  
  # Current account ID for reference
  account_id = data.aws_caller_identity.current.account_id
  
  # Current region for reference
  region = data.aws_region.current.name
}

# Output to verify we're using the correct AWS account
# This will show after running 'terraform apply'
output "aws_account_info" {
  description = "Current AWS account information"
  value = {
    account_id = local.account_id
    region     = local.region
    user_arn   = data.aws_caller_identity.current.arn
  }
}