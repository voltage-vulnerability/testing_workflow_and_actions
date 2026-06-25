provider "aws" {
  region = "us-east-1"
}

# 1. CRITICAL: Hardcoded Plaintext AWS Access Keys
# Scanner Check: AWS_001 / CKV_AWS_41
resource "aws_iam_user_login_profile" "vulnerable_user" {
  user    = "test-admin"
  pgp_key = "keybase:some_user" # Normally required to encrypt, but we are simulating static credential risks
}

# 2. HIGH: S3 Bucket with Public Read Access and Missing Encryption
# Scanner Check: AWS_002 / CKV_AWS_20 / CKV_AWS_19
resource "aws_s3_bucket" "vulnerable_bucket" {
  bucket = "my-highly-insecure-test-bucket-12345"
}

resource "aws_s3_bucket_public_access_block" "vulnerable_bucket_acl" {
  bucket = aws_s3_bucket.vulnerable_bucket.id

  # Setting these to false explicitly allows public data exposure
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# 3. CRITICAL: Security Group Open to the Entire Internet (0.0.0.0/0) on Sensitive Ports
# Scanner Check: AWS_008 / CKV_AWS_24
resource "aws_security_group" "vulnerable_sg" {
  name        = "vulnerable-sg"
  description = "Allow SSH and RDP from anywhere"

  ingress {
    description = "SSH open to world"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Vulnerability: Broad CIDR range
  }

  ingress {
    description = "RDP open to world"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Vulnerability: Broad CIDR range
  }
}

# 4. HIGH: Publicly Accessible RDS Database Instance with No Encryption
# Scanner Check: AWS_011 / CKV_AWS_133
resource "aws_db_instance" "vulnerable_rds" {
  allocated_storage    = 10
  engine               = "mysql"
  engine_version       = "8.0"
  instance_class       = "db.t3.micro"
  db_name              = "insecuredb"
  username             = "admin"
  password             = "SuperSecretPassword123!" # Vulnerability: Hardcoded plain password
  publicly_accessible  = true                     # Vulnerability: Exposed to internet
  skip_final_snapshot  = true
  storage_encrypted    = false                    # Vulnerability: Data at rest is unencrypted
}
