# security.tf - Security Group Configuration
# Security Groups are like firewalls that control network traffic to/from your EC2 instance
# They work at the instance level and are stateful (return traffic is automatically allowed)

# Main Security Group for the RAG Application
resource "aws_security_group" "rag_sg" {
  name        = "${var.project_name}-sg"
  description = "Security group for RAG Assistant EC2 instance"
  
  # VPC ID will be automatically set to the default VPC
  # In production, you might want to create a custom VPC
  
  # INGRESS RULES - What can come IN to the server
  
  # Rule 1: SSH Access (Port 22)
  # Needed to connect to the server for management
  ingress {
    description = "SSH access for server management"
    from_port   = 22                    # SSH port
    to_port     = 22                    # Same port (not a range)
    protocol    = "tcp"                 # SSH uses TCP protocol
    cidr_blocks = [var.allowed_ssh_ip]  # Who can connect (0.0.0.0/0 = anyone)
    
    # Security tip: Change var.allowed_ssh_ip to your specific IP address
    # Find your IP: curl ifconfig.me
    # Then use: "YOUR.IP.ADDRESS/32" instead of "0.0.0.0/0"
  }
  
  # Rule 2: HTTP Access (Port 80)
  # For web traffic to your application
  ingress {
    description = "HTTP web traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Allow from anywhere (public website)
    
    # This is where users will access your Gradio interface
  }
  
  # Rule 3: HTTPS Access (Port 443)
  # For secure web traffic (if you add SSL later)
  ingress {
    description = "HTTPS secure web traffic"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Allow from anywhere
    
    # You'll use this if you add SSL certificates later
  }
  
  # Optional: Direct access to Gradio (Port 7860)
  # Uncomment if you want to access Gradio directly without nginx
  # ingress {
  #   description = "Gradio UI direct access"
  #   from_port   = 7860
  #   to_port     = 7860
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"]
  # }
  
  # Optional: Direct access to FastAPI (Port 8000)
  # Uncomment for API testing without going through nginx
  # ingress {
  #   description = "FastAPI direct access"
  #   from_port   = 8000
  #   to_port     = 8000
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"]
  # }
  
  # EGRESS RULES - What can go OUT from the server
  
  # Allow all outbound traffic
  # The server needs to:
  # - Download packages and updates
  # - Pull Docker images
  # - Access S3 for PDFs
  # - Call external APIs (LLM service)
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"  # -1 means all protocols
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  # Tags for organization
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-security-group"
    Type = "security-group"
  })
  
  # Lifecycle rule to handle changes gracefully
  lifecycle {
    create_before_destroy = true
  }
}

# Optional: Additional security group for database access only
# Uncomment if you want to separate database traffic
# resource "aws_security_group" "database_sg" {
#   name        = "${var.project_name}-database-sg"
#   description = "Security group for database access"
#   
#   # Only allow traffic from the main security group
#   ingress {
#     description     = "Qdrant database access"
#     from_port       = 6333
#     to_port         = 6333
#     protocol        = "tcp"
#     security_groups = [aws_security_group.rag_sg.id]  # Only from app server
#   }
#   
#   tags = merge(local.common_tags, {
#     Name = "${var.project_name}-database-sg"
#   })
# }

# Security Best Practices Notes:
# 1. Always use the principle of least privilege
# 2. Restrict SSH to specific IPs when possible
# 3. Use separate security groups for different tiers (web, app, database)
# 4. Regularly review and audit your security group rules
# 5. Consider using AWS Systems Manager Session Manager instead of SSH
# 6. Enable VPC Flow Logs to monitor network traffic