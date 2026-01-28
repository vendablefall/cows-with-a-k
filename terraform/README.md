# Terraform Infrastructure

This directory contains Terraform configuration to deploy the Cows with a K infrastructure to AWS.

## Architecture

The infrastructure includes:
- **DynamoDB Tables**: Users, Messages, TokenBlacklist
- **Lambda Functions**: 7 functions for authentication and message board
- **API Gateway**: REST API with all endpoints configured
- **S3 Bucket**: Frontend hosting with static website configuration

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** >= 1.0 installed ([Download](https://www.terraform.io/downloads))
3. **AWS CLI** configured with credentials
4. **Python Dependencies** packaged as Lambda layer

## Setup Instructions

### 1. Prepare Lambda Layer

First, create a Lambda layer with Python dependencies:

```bash
# Create layer directory structure
mkdir -p lambda-layer/python

# Install dependencies into the layer
pip install -r ../lambda/requirements.txt -t lambda-layer/python/

# The layer will be automatically zipped by Terraform
```

### 2. Configure Variables

Create a `terraform.tfvars` file (or use environment variables):

```hcl
aws_region   = "us-east-1"
project_name = "CowsWithAK"
environment  = "prod"
jwt_secret   = "your-secure-jwt-secret-here"  # CHANGE THIS!
admin_email  = "admin@yourdomian.com"
ses_sender   = "noreply@yourdomain.com"
```

**Important**: Change the `jwt_secret` to a secure random string in production!

### 3. Verify SES Email

Before deploying, verify your sender email in AWS SES:

```bash
aws ses verify-email-identity --email-address noreply@yourdomain.com
```

Check the verification email and click the confirmation link.

### 4. Initialize Terraform

```bash
cd terraform
terraform init
```

### 5. Review the Plan

```bash
terraform plan
```

This shows you what resources will be created.

### 6. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm.

### 7. Get API Gateway URL

After deployment, Terraform will output the API Gateway URL:

```bash
terraform output api_gateway_url
```

Example output: `https://abc123def.execute-api.us-east-1.amazonaws.com/prod`

### 8. Update Frontend Configuration

Update the `API_BASE_URL` in your frontend application:

```typescript
// index.tsx
const API_BASE_URL = 'https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod';
```

### 9. Build and Deploy Frontend

```bash
# Build the frontend
npm run build

# Upload to S3 bucket (get bucket name from Terraform output)
aws s3 sync dist/ s3://$(terraform output -raw frontend_bucket_name) --delete
```

Or use the website endpoint directly:

```bash
terraform output frontend_website_url
```

## Managing the Infrastructure

### View Outputs

```bash
terraform output
```

### Update Resources

After modifying any `.tf` files:

```bash
terraform plan
terraform apply
```

### Destroy Infrastructure

To remove all resources (⚠️ **WARNING**: This deletes all data):

```bash
terraform destroy
```

## Resource Details

### DynamoDB Tables

- **CowsWithAK-Users**
  - Primary Key: `email`
  - Billing: Pay-per-request
  - Attributes: userId, username, passwordHash, status, clearanceLevel, etc.

- **CowsWithAK-Messages**
  - Primary Key: `messageId`
  - GSI: `timestamp-index` (for chronological retrieval)
  - Billing: Pay-per-request

- **CowsWithAK-TokenBlacklist**
  - Primary Key: `token`
  - TTL enabled on `ttl` attribute
  - Billing: Pay-per-request

### Lambda Functions

All Lambda functions use:
- Runtime: Python 3.11
- Timeout: 30 seconds
- IAM Role: Shared role with DynamoDB and SES permissions
- Layer: PyJWT and boto3 dependencies

Functions:
1. `signin` - POST /auth/signin
2. `signup` - POST /auth/signup
3. `signout` - POST /auth/signout
4. `get-current-user` - GET /auth/me
5. `get-messages` - GET /messages
6. `post-message` - POST /messages
7. `delete-message` - DELETE /messages/{messageId}

### API Gateway

- Type: REST API
- Stage: Configurable (default: `prod`)
- CORS: Enabled on all endpoints
- Authentication: JWT tokens in Authorization header

## Security Considerations

1. **JWT Secret**: Change the default JWT secret to a strong random value
2. **SES**: Verify sender email addresses in production
3. **IAM Permissions**: Lambda functions have DynamoDB and SES access
4. **S3 Bucket**: Frontend bucket is publicly readable (required for website hosting)
5. **API Gateway**: No built-in rate limiting (consider adding AWS WAF)

## Monitoring

View Lambda logs in CloudWatch:

```bash
# Example: View signin Lambda logs
aws logs tail /aws/lambda/CowsWithAK-signin --follow
```

## Troubleshooting

### Lambda Layer Issues

If you get import errors in Lambda:
1. Ensure dependencies are installed in `lambda-layer/python/` directory
2. Check Python version compatibility (must be 3.11)
3. Verify the layer is attached to all Lambda functions

### SES Email Not Sending

1. Check SES is in production mode (not sandbox)
2. Verify sender email address: `aws ses list-verified-email-addresses`
3. Check Lambda CloudWatch logs for error messages

### CORS Errors

The Lambda functions include CORS headers. If you still get CORS errors:
1. Verify OPTIONS methods are configured in API Gateway
2. Check the Lambda function response includes proper CORS headers
3. Ensure frontend origin matches allowed origins

### API Gateway 403 Errors

1. Check Lambda permissions allow API Gateway invocation
2. Verify the Lambda function handler name is correct
3. Check API Gateway deployment was successful

## Cost Estimation

Typical monthly costs (assuming moderate usage):
- DynamoDB: $5-20 (pay-per-request)
- Lambda: $5-15 (1M requests = ~$1)
- API Gateway: $3.50/million requests
- S3: $1-5 for storage and bandwidth
- **Estimated Total**: $15-40/month

## Support

For issues or questions:
- Check Lambda logs in CloudWatch
- Review API Gateway execution logs
- Verify DynamoDB table data
- Ensure all environment variables are set correctly
