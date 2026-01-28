#!/bin/bash

# Deployment script for Cows with a K infrastructure
# This script automates the deployment process

set -e

echo "🐄 Cows with a K - Infrastructure Deployment Script"
echo "=================================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Terraform
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install AWS CLI first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

echo "✅ All prerequisites met"
echo ""

# Step 1: Create Lambda Layer
echo "Step 1: Creating Lambda layer with dependencies..."
if [ ! -d "lambda-layer/python" ]; then
    mkdir -p lambda-layer/python
fi

pip install -r ../lambda/requirements.txt -t lambda-layer/python/ --quiet
echo "✅ Lambda layer created"
echo ""

# Step 2: Initialize Terraform
echo "Step 2: Initializing Terraform..."
terraform init
echo "✅ Terraform initialized"
echo ""

# Step 3: Validate Configuration
echo "Step 3: Validating Terraform configuration..."
terraform validate
echo "✅ Configuration valid"
echo ""

# Step 4: Plan
echo "Step 4: Creating deployment plan..."
terraform plan -out=tfplan
echo "✅ Plan created"
echo ""

# Step 5: Confirm deployment
read -p "Do you want to apply this plan? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled"
    exit 0
fi

# Step 6: Apply
echo "Step 6: Deploying infrastructure..."
terraform apply tfplan
echo "✅ Infrastructure deployed"
echo ""

# Step 7: Show outputs
echo "Step 7: Deployment summary"
echo "=========================="
echo ""
terraform output
echo ""

# Save API URL to file for easy access
API_URL=$(terraform output -raw api_gateway_url)
echo "$API_URL" > ../api-gateway-url.txt

echo "✅ API Gateway URL saved to api-gateway-url.txt"
echo ""
echo "Next steps:"
echo "1. Update index.tsx with API_BASE_URL: $API_URL"
echo "2. Build frontend: npm run build"
echo "3. Deploy frontend: aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket_name)"
echo "4. Access your site at: http://$(terraform output -raw frontend_website_url)"
echo ""
echo "🐄 Deployment complete! Moo!"
