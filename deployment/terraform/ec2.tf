# ec2.tf - EC2 Instance Configuration
# This file defines our virtual server in AWS

# Data source to get the latest Ubuntu 22.04 AMI
# AMI = Amazon Machine Image (like a template for the OS)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical's AWS account ID (Ubuntu's publisher)

  # Filters to find the right Ubuntu image
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
    # jammy = Ubuntu 22.04 codename
    # hvm-ssd = Hardware Virtual Machine with SSD storage
    # amd64 = 64-bit architecture (works on Intel too)
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]  # Hardware Virtual Machine (modern, faster)
  }
}

# The EC2 Instance Resource - Our Virtual Server
resource "aws_instance" "rag_server" {
  # Which operating system image to use
  ami           = data.aws_ami.ubuntu.id
  
  # Instance size (CPU and memory)
  instance_type = var.instance_type
  
  # SSH key for remote access
  key_name      = var.key_pair_name
  
  # Security group (firewall rules) - defined in security.tf
  vpc_security_group_ids = [aws_security_group.rag_sg.id]
  
  # IAM role for S3 access - defined in iam.tf
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  
  # Storage configuration
  root_block_device {
    volume_size = var.root_volume_size  # Size in GB
    volume_type = "gp3"                 # General Purpose SSD v3 (good performance, cost-effective)
    encrypted   = true                  # Encrypt data at rest for security
    
    # Optional: Set IOPS and throughput for gp3
    # iops       = 3000  # Default is 3000
    # throughput = 125   # Default is 125 MB/s
    
    tags = merge(local.common_tags, {
      Name = "${var.project_name}-root-volume"
    })
  }
  
  # Script that runs when instance first starts
  # We'll create this file next - it installs Docker, etc.
  user_data = file("${path.module}/user-data.sh")
  
  # Enable detailed monitoring (1-minute intervals instead of 5-minute)
  # monitoring = true  # Costs extra ~$2/month, uncomment if needed
  
  # Tags for organization and billing
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-server"
    Type = "application-server"
  })
  
  # Ensure we create the instance before destroying the old one during updates
  lifecycle {
    create_before_destroy = true
  }
}

# Elastic IP - A Static Public IP Address
# Without this, the IP changes every time the instance restarts
resource "aws_eip" "rag_eip" {
  instance = aws_instance.rag_server.id
  domain   = "vpc"  # For VPC instances (modern AWS setup)
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-eip"
    Type = "elastic-ip"
  })
  
  # Make sure the instance exists before attaching the IP
  depends_on = [aws_instance.rag_server]
}

# Optional: Create an EBS Volume for persistent data
# Uncomment if you want separate storage for Qdrant data
# resource "aws_ebs_volume" "data_volume" {
#   availability_zone = aws_instance.rag_server.availability_zone
#   size              = 20
#   type              = "gp3"
#   encrypted         = true
#   
#   tags = merge(local.common_tags, {
#     Name = "${var.project_name}-data-volume"
#   })
# }

# Optional: Attach the data volume to the instance
# resource "aws_volume_attachment" "data_attachment" {
#   device_name = "/dev/sdf"
#   volume_id   = aws_ebs_volume.data_volume.id
#   instance_id = aws_instance.rag_server.id
# }