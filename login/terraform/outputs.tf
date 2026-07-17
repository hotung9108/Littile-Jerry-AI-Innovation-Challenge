output "api_endpoint" {
  description = "Base URL của API Gateway (gọi POST {api_endpoint}/login)"
  value       = module.api_gateway_login.api_endpoint
}

output "users_table_name" {
  value = module.users_table.dynamodb_table_id
}

output "lambda_function_name" {
  value = module.lambda_login.lambda_function_name
}
