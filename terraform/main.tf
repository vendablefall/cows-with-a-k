terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ============================================
# DynamoDB Tables
# ============================================

resource "aws_dynamodb_table" "users" {
  name           = "${var.project_name}-Users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "email"

  attribute {
    name = "email"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-Users"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "token_blacklist" {
  name           = "${var.project_name}-TokenBlacklist"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "token"

  attribute {
    name = "token"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-TokenBlacklist"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "messages" {
  name           = "${var.project_name}-Messages"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "messageId"

  attribute {
    name = "messageId"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  global_secondary_index {
    name            = "timestamp-index"
    hash_key        = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-Messages"
    Project     = var.project_name
    Environment = var.environment
  }
}

# ============================================
# IAM Role for Lambda Functions
# ============================================

resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-lambda-role"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.users.arn,
          aws_dynamodb_table.token_blacklist.arn,
          aws_dynamodb_table.messages.arn,
          "${aws_dynamodb_table.messages.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail"
        ]
        Resource = "*"
      }
    ]
  })
}

# ============================================
# Lambda Layer for Dependencies
# ============================================

data "archive_file" "lambda_layer" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda-layer/python"
  output_path = "${path.module}/lambda-layer.zip"
}

resource "aws_lambda_layer_version" "dependencies" {
  filename            = data.archive_file.lambda_layer.output_path
  layer_name          = "${var.project_name}-dependencies"
  compatible_runtimes = ["python3.11"]
  source_code_hash    = data.archive_file.lambda_layer.output_base64sha256

  description = "PyJWT and boto3 dependencies for Lambda functions"
}

# ============================================
# Lambda Functions
# ============================================

# Sign In Lambda
data "archive_file" "signin_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/signin.py"
  output_path = "${path.module}/signin.zip"
}

resource "aws_lambda_function" "signin" {
  filename         = data.archive_file.signin_lambda.output_path
  function_name    = "${var.project_name}-signin"
  role            = aws_iam_role.lambda_role.arn
  handler         = "signin.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  source_code_hash = data.archive_file.signin_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.users.name
      JWT_SECRET  = var.jwt_secret
    }
  }

  tags = {
    Name        = "${var.project_name}-signin"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Sign Up Lambda
data "archive_file" "signup_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/signup.py"
  output_path = "${path.module}/signup.zip"
}

resource "aws_lambda_function" "signup" {
  filename         = data.archive_file.signup_lambda.output_path
  function_name    = "${var.project_name}-signup"
  role            = aws_iam_role.lambda_role.arn
  handler         = "signup.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  source_code_hash = data.archive_file.signup_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      USERS_TABLE = aws_dynamodb_table.users.name
      ADMIN_EMAIL = var.admin_email
      SES_SENDER  = var.ses_sender
    }
  }

  tags = {
    Name        = "${var.project_name}-signup"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Sign Out Lambda
data "archive_file" "signout_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/signout.py"
  output_path = "${path.module}/signout.zip"
}

resource "aws_lambda_function" "signout" {
  filename         = data.archive_file.signout_lambda.output_path
  function_name    = "${var.project_name}-signout"
  role            = aws_iam_role.lambda_role.arn
  handler         = "signout.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  source_code_hash = data.archive_file.signout_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      BLACKLIST_TABLE = aws_dynamodb_table.token_blacklist.name
      JWT_SECRET      = var.jwt_secret
    }
  }

  tags = {
    Name        = "${var.project_name}-signout"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Get Current User Lambda
data "archive_file" "get_current_user_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/get_current_user.py"
  output_path = "${path.module}/get_current_user.zip"
}

resource "aws_lambda_function" "get_current_user" {
  filename         = data.archive_file.get_current_user_lambda.output_path
  function_name    = "${var.project_name}-get-current-user"
  role            = aws_iam_role.lambda_role.arn
  handler         = "get_current_user.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  source_code_hash = data.archive_file.get_current_user_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      USERS_TABLE     = aws_dynamodb_table.users.name
      BLACKLIST_TABLE = aws_dynamodb_table.token_blacklist.name
      JWT_SECRET      = var.jwt_secret
    }
  }

  tags = {
    Name        = "${var.project_name}-get-current-user"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Get Messages Lambda
data "archive_file" "get_messages_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/get_messages.py"
  output_path = "${path.module}/get_messages.zip"
}

resource "aws_lambda_function" "get_messages" {
  filename         = data.archive_file.get_messages_lambda.output_path
  function_name    = "${var.project_name}-get-messages"
  role            = aws_iam_role.lambda_role.arn
  handler         = "get_messages.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  source_code_hash = data.archive_file.get_messages_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      MESSAGES_TABLE  = aws_dynamodb_table.messages.name
      BLACKLIST_TABLE = aws_dynamodb_table.token_blacklist.name
      JWT_SECRET      = var.jwt_secret
    }
  }

  tags = {
    Name        = "${var.project_name}-get-messages"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Post Message Lambda
data "archive_file" "post_message_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/post_message.py"
  output_path = "${path.module}/post_message.zip"
}

resource "aws_lambda_function" "post_message" {
  filename         = data.archive_file.post_message_lambda.output_path
  function_name    = "${var.project_name}-post-message"
  role            = aws_iam_role.lambda_role.arn
  handler         = "post_message.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  source_code_hash = data.archive_file.post_message_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      MESSAGES_TABLE  = aws_dynamodb_table.messages.name
      USERS_TABLE     = aws_dynamodb_table.users.name
      BLACKLIST_TABLE = aws_dynamodb_table.token_blacklist.name
      JWT_SECRET      = var.jwt_secret
    }
  }

  tags = {
    Name        = "${var.project_name}-post-message"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Delete Message Lambda
data "archive_file" "delete_message_lambda" {
  type        = "zip"
  source_file = "${path.module}/../lambda/delete_message.py"
  output_path = "${path.module}/delete_message.zip"
}

resource "aws_lambda_function" "delete_message" {
  filename         = data.archive_file.delete_message_lambda.output_path
  function_name    = "${var.project_name}-delete-message"
  role            = aws_iam_role.lambda_role.arn
  handler         = "delete_message.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  source_code_hash = data.archive_file.delete_message_lambda.output_base64sha256

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      MESSAGES_TABLE  = aws_dynamodb_table.messages.name
      USERS_TABLE     = aws_dynamodb_table.users.name
      BLACKLIST_TABLE = aws_dynamodb_table.token_blacklist.name
      JWT_SECRET      = var.jwt_secret
    }
  }

  tags = {
    Name        = "${var.project_name}-delete-message"
    Project     = var.project_name
    Environment = var.environment
  }
}

# ============================================
# API Gateway (using OpenAPI Specification)
# ============================================

# Prepare OpenAPI spec with Lambda integrations
locals {
  openapi_spec = templatefile("${path.module}/api-spec-template.yaml", {
    aws_region             = var.aws_region
    environment            = var.environment
    signin_lambda_arn      = aws_lambda_function.signin.invoke_arn
    signup_lambda_arn      = aws_lambda_function.signup.invoke_arn
    signout_lambda_arn     = aws_lambda_function.signout.invoke_arn
    get_current_user_arn   = aws_lambda_function.get_current_user.invoke_arn
    get_messages_arn       = aws_lambda_function.get_messages.invoke_arn
    post_message_arn       = aws_lambda_function.post_message.invoke_arn
    delete_message_arn     = aws_lambda_function.delete_message.invoke_arn
  })
}

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-api"
  description = "API Gateway for Cows with a K authentication and message board"

  body = local.openapi_spec

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name        = "${var.project_name}-api"
    Project     = var.project_name
    Environment = var.environment
  }
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(local.openapi_spec)
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_rest_api.main
  ]
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  tags = {
    Name        = "${var.project_name}-api-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Lambda Permissions for API Gateway
resource "aws_lambda_permission" "signin_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signin.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "signup_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signup.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "signout_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.signout.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "get_current_user_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_current_user.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "get_messages_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_messages.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "post_message_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.post_message.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "delete_message_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.delete_message.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# ============================================
# S3 Bucket for Frontend Hosting
# ============================================

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-frontend-${var.environment}"

  tags = {
    Name        = "${var.project_name}-frontend"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.frontend]
}

resource "aws_s3_bucket_cors_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
