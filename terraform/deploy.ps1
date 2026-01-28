# Deployment script for Cows with a K infrastructure (PowerShell version)
# This script automates the deployment process

$ErrorActionPreference = "Stop"

Write-Host "🐄 Cows with a K - Infrastructure Deployment Script" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Terraform
if (-not (Get-Command terraform -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Terraform is not installed. Please install Terraform first." -ForegroundColor Red
    exit 1
}

# Check AWS CLI
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI is not installed. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check AWS credentials
try {
    aws sts get-caller-identity | Out-Null
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    exit 1
}

Write-Host "✅ All prerequisites met" -ForegroundColor Green
Write-Host ""

# Step 1: Create Lambda Layer
Write-Host "Step 1: Creating Lambda layer with dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "lambda-layer\python")) {
    New-Item -ItemType Directory -Path "lambda-layer\python" -Force | Out-Null
}

pip install -r ..\lambda\requirements.txt -t lambda-layer\python\ --quiet
Write-Host "✅ Lambda layer created" -ForegroundColor Green
Write-Host ""

# Step 2: Initialize Terraform
Write-Host "Step 2: Initializing Terraform..." -ForegroundColor Yellow
terraform init
Write-Host "✅ Terraform initialized" -ForegroundColor Green
Write-Host ""

# Step 3: Validate Configuration
Write-Host "Step 3: Validating Terraform configuration..." -ForegroundColor Yellow
terraform validate
Write-Host "✅ Configuration valid" -ForegroundColor Green
Write-Host ""

# Step 4: Plan
Write-Host "Step 4: Creating deployment plan..." -ForegroundColor Yellow
terraform plan -out=tfplan
Write-Host "✅ Plan created" -ForegroundColor Green
Write-Host ""

# Step 5: Confirm deployment
$confirm = Read-Host "Do you want to apply this plan? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Deployment cancelled" -ForegroundColor Yellow
    exit 0
}

# Step 6: Apply
Write-Host "Step 6: Deploying infrastructure..." -ForegroundColor Yellow
terraform apply tfplan
Write-Host "✅ Infrastructure deployed" -ForegroundColor Green
Write-Host ""

# Step 7: Show outputs
Write-Host "Step 7: Deployment summary" -ForegroundColor Yellow
Write-Host "==========================" -ForegroundColor Yellow
Write-Host ""
terraform output
Write-Host ""

# Save API URL to file for easy access
$apiUrl = terraform output -raw api_gateway_url
$apiUrl | Out-File -FilePath "..\api-gateway-url.txt" -Encoding utf8

Write-Host "✅ API Gateway URL saved to api-gateway-url.txt" -ForegroundColor Green
Write-Host ""

$frontendBucket = terraform output -raw frontend_bucket_name
$websiteUrl = terraform output -raw frontend_website_url

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Update index.tsx with API_BASE_URL: $apiUrl" -ForegroundColor White
Write-Host "2. Build frontend: npm run build" -ForegroundColor White
Write-Host "3. Deploy frontend: aws s3 sync dist/ s3://$frontendBucket --delete" -ForegroundColor White
Write-Host "4. Access your site at: http://$websiteUrl" -ForegroundColor White
Write-Host ""
Write-Host "🐄 Deployment complete! Moo!" -ForegroundColor Green
