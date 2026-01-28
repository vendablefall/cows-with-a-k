variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "CowsWithAK"
}

variable "environment" {
  description = "Environment name (prod, dev, staging)"
  type        = string
  default     = "prod"
}

variable "jwt_secret" {
  description = "Secret key for JWT token signing (change in production)"
  type        = string
  sensitive   = true
  default     = "moo-secret-key-change-in-production"
}

variable "admin_email" {
  description = "Admin email for new user registration notifications"
  type        = string
  default     = "admin@cowswithak.com"
}

variable "ses_sender" {
  description = "SES verified sender email address"
  type        = string
  default     = "noreply@cowswithak.com"
}
