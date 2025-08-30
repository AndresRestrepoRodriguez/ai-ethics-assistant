# outputs.tf - Terraform Output Values
# Outputs are like "return values" from Terraform
# They show important information after resources are created

# Output 1: The public IP address of your server
output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_eip.rag_eip.public_ip
  
  # This is the IP you'll use to access your application
  # Example: http://54.123.45.67
}

# Output 2: The EC2 instance ID
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.rag_server.id
  
  # Useful for AWS CLI commands like:
  # aws ec2 describe-instances --instance-ids i-1234567890abcdef0
}

# Output 3: SSH command to connect to the server
output "ssh_command" {
  description = "Command to SSH into the instance"
  value       = "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.rag_eip.public_ip}"
  
  # Just copy and paste this command to connect!
  # Make sure your key file has the right permissions (chmod 400)
}

# Output 4: Application URLs
output "application_urls" {
  description = "URLs to access your application"
  value = {
    main_app     = "http://${aws_eip.rag_eip.public_ip}"
    api_docs     = "http://${aws_eip.rag_eip.public_ip}/docs"
    health_check = "http://${aws_eip.rag_eip.public_ip}/internal/health"
  }
  
  # These are the URLs you'll use to access different parts of your app
}

# Output 5: Instance details for reference
output "instance_details" {
  description = "Detailed information about the EC2 instance"
  value = {
    instance_type     = aws_instance.rag_server.instance_type
    availability_zone = aws_instance.rag_server.availability_zone
    ami_id           = aws_instance.rag_server.ami
    security_group   = aws_security_group.rag_sg.id
  }
  
  # Useful for debugging and documentation
}

# Output 6: S3 bucket configuration reminder
output "s3_configuration" {
  description = "S3 bucket configuration"
  value = {
    bucket_name = var.s3_bucket_name
    iam_role   = aws_iam_role.ec2_role.name
    note       = "The EC2 instance has read access to this bucket via IAM role"
  }
}

# Output 7: Next steps after deployment
output "next_steps" {
  description = "What to do after Terraform completes"
  value = <<-EOT
    
    ========================================
    🎉 Infrastructure created successfully!
    ========================================
    
    Next steps:
    1. SSH into the server:
       ${aws_eip.rag_eip.public_ip != "" ? "ssh -i ~/.ssh/${var.key_pair_name}.pem ubuntu@${aws_eip.rag_eip.public_ip}" : "Waiting for IP..."}
    
    2. Clone your repository:
       git clone https://github.com/yourusername/rag-project.git
       cd rag-project
    
    3. Set up environment variables:
       cp .env.example .env
       nano .env  # Add your API keys
    
    4. Start the application:
       docker compose up -d
    
    5. Access your application:
       Main App: http://${aws_eip.rag_eip.public_ip != "" ? aws_eip.rag_eip.public_ip : "Waiting for IP..."}
       API Docs: http://${aws_eip.rag_eip.public_ip != "" ? aws_eip.rag_eip.public_ip : "Waiting for IP..."}/docs
    
    6. Check logs:
       docker compose logs -f
    
    ========================================
  EOT
  
  # This will be displayed after 'terraform apply' completes
}

# How to use outputs:
# 
# After running 'terraform apply':
# - All outputs are displayed automatically
# 
# To see outputs again later:
# - terraform output                    # Show all outputs
# - terraform output instance_public_ip # Show specific output
# - terraform output -json             # Get outputs as JSON
# 
# You can also use outputs in scripts:
# IP=$(terraform output -raw instance_public_ip)
# ssh -i ~/.ssh/rag-assistant-key.pem ubuntu@$IP