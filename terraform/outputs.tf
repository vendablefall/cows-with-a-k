output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "api_gateway_id" {
  description = "API Gateway REST API ID"
  value       = aws_api_gateway_rest_api.main.id
}

output "frontend_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_website_url" {
  description = "S3 website endpoint URL"
  value       = aws_s3_bucket_website_configuration.frontend.website_endpoint
}

output "users_table_name" {
  description = "DynamoDB Users table name"
  value       = aws_dynamodb_table.users.name
}

output "messages_table_name" {
  description = "DynamoDB Messages table name"
  value       = aws_dynamodb_table.messages.name
}

output "token_blacklist_table_name" {
  description = "DynamoDB Token Blacklist table name"
  value       = aws_dynamodb_table.token_blacklist.name
}

output "lambda_functions" {
  description = "Lambda function names"
  value = {
    signin           = aws_lambda_function.signin.function_name
    signup           = aws_lambda_function.signup.function_name
    signout          = aws_lambda_function.signout.function_name
    get_current_user = aws_lambda_function.get_current_user.function_name
    get_messages     = aws_lambda_function.get_messages.function_name
    post_message     = aws_lambda_function.post_message.function_name
    delete_message   = aws_lambda_function.delete_message.function_name
  }
}
