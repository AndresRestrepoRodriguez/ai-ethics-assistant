# iam.tf - IAM (Identity and Access Management) Configuration
# IAM controls WHO can do WHAT with your AWS resources
# We need to give our EC2 instance permission to access S3

# Step 1: Create an IAM Role
# A role is like a set of permissions that can be assumed by AWS services
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"
  
  # This policy says "EC2 instances can assume this role"
  # It's like saying "this badge can be worn by EC2 instances"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"  # Policy language version (not a date!)
    Statement = [
      {
        Action = "sts:AssumeRole"  # sts = Security Token Service
        Effect = "Allow"            # Allow (not Deny)
        Principal = {
          Service = "ec2.amazonaws.com"  # Only EC2 can use this role
        }
      }
    ]
  })
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-ec2-iam-role"
    Type = "iam-role"
  })
}

# Step 2: Define What the Role Can Do (Policy)
# This policy gives read access to your S3 bucket
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_name}-s3-access-policy"
  role = aws_iam_role.ec2_role.id
  
  # The actual permissions
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3BucketAccess"  # Statement ID for documentation
        Effect = "Allow"
        Action = [
          "s3:GetObject",        # Can download files
          "s3:ListBucket",       # Can list files in bucket
          "s3:GetBucketLocation" # Can get bucket metadata
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",     # The bucket itself
          "arn:aws:s3:::${var.s3_bucket_name}/*"    # All objects in the bucket
        ]
      },
      {
        Sid    = "AllowS3ListAllBuckets"
        Effect = "Allow"
        Action = "s3:ListAllMyBuckets"  # Can list all buckets (needed for boto3)
        Resource = "*"
      }
    ]
  })
}

# Optional: Add CloudWatch Logs permissions for monitoring
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "${var.project_name}-cloudwatch-logs-policy"
  role = aws_iam_role.ec2_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${local.region}:${local.account_id}:*"
      }
    ]
  })
}

# Step 3: Create an Instance Profile
# This is the "bridge" that connects the IAM role to the EC2 instance
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-instance-profile"
  role = aws_iam_role.ec2_role.name
  
  tags = merge(local.common_tags, {
    Name = "${var.project_name}-instance-profile"
    Type = "iam-instance-profile"
  })
}

# How This Works:
# 1. The IAM Role defines a set of permissions
# 2. The Role Policy specifies exactly what actions are allowed
# 3. The Instance Profile attaches the role to the EC2 instance
# 4. When your app runs on EC2, it automatically gets these permissions
# 5. No need to store AWS credentials on the server! (More secure)

# Security Benefits:
# - No hardcoded credentials in your application
# - Permissions are temporary and rotated automatically
# - Can be revoked instantly if needed
# - Follows AWS best practices for security

# To Test This Later:
# SSH into your EC2 instance and run:
# aws s3 ls s3://your-bucket-name/
# It should work without any AWS credentials configured!