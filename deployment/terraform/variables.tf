# variables.tf - Input Variables for Terraform Configuration
# Variables allow us to customize our infrastructure without changing code
# Think of them as function parameters or environment variables

# AWS Region Variable
variable "aws_region" {
  description = "AWS region where resources will be created"
  type        = string
  default     = "us-east-1"
  
  # You can override this default in terraform.tfvars or via command line:
  # terraform apply -var="aws_region=us-west-2"
}

# EC2 Instance Type Variable
variable "instance_type" {
  description = "EC2 instance type - determines CPU, memory, and network capacity"
  type        = string
  default     = "t3.small"  # 2 vCPU, 2GB RAM - good for small applications
  
  # Common alternatives:
  # t3.micro  - 2 vCPU, 1GB RAM  (~$8/month)  - minimum for our app
  # t3.small  - 2 vCPU, 2GB RAM  (~$15/month) - recommended
  # t3.medium - 2 vCPU, 4GB RAM  (~$30/month) - if you need more memory
  
  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Instance type should be a t3 instance for cost optimization."
  }
}

# SSH Key Pair Name
variable "key_pair_name" {
  description = "Name of the AWS SSH key pair for EC2 access"
  type        = string
  default     = "rag-assistant-key"
  
  # This should match the key pair you created earlier with:
  # aws ec2 create-key-pair --key-name rag-assistant-key
}

# S3 Bucket for PDFs
variable "s3_bucket_name" {
  description = "Name of the S3 bucket containing your PDF documents"
  type        = string
  # No default - this MUST be provided by the user
  
  validation {
    condition     = length(var.s3_bucket_name) > 3
    error_message = "S3 bucket name must be at least 3 characters long."
  }
}

# Project Name for Tagging
variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "rag-assistant"
  
  # This will be used to name resources like:
  # - rag-assistant-server (EC2 instance)
  # - rag-assistant-sg (Security Group)
  # - rag-assistant-role (IAM Role)
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.project_name))
    error_message = "Project name must start with a letter and contain only lowercase letters, numbers, and hyphens."
  }
}

# Optional: Allow SSH from specific IP only (more secure)
variable "allowed_ssh_ip" {
  description = "Your IP address for SSH access (leave as 0.0.0.0/0 for anywhere)"
  type        = string
  default     = "0.0.0.0/0"  # Allow from anywhere - change this for better security!
  
  # To find your IP: curl ifconfig.me
  # Then set this to: "YOUR.IP.ADDRESS/32"
}

# Optional: Instance Volume Size
variable "root_volume_size" {
  description = "Size of the root EBS volume in GB"
  type        = number
  default     = 30
  
  validation {
    condition     = var.root_volume_size >= 20 && var.root_volume_size <= 100
    error_message = "Root volume size must be between 20 and 100 GB."
  }
}

# Optional: Environment Tag
variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}