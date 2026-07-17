# Trước khi chạy `terraform apply`, phải cài production dependencies trong login/:
#   npm ci --omit=dev
# Module tự đóng gói (zip) code + node_modules sẵn có, không tự chạy npm install.

module "lambda_login" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name = "${var.project_name}-login-${var.environment}"
  handler       = "src/lambda.handler"
  runtime       = "nodejs20.x"
  timeout       = 10
  memory_size   = 256

  source_path = [
    {
      path = "${path.module}/.."
      patterns = [
        "!terraform/.*",
        "!\\.git/.*",
        "!\\.env$",
        "!\\.env\\.example$",
        "!\\.envrc$",
        "!\\.envrc\\.example$",
      ]
    }
  ]

  environment_variables = {
    USERS_TABLE    = module.users_table.dynamodb_table_id
    EMAIL_INDEX    = local.email_index_name
    JWT_SECRET     = var.jwt_secret
    JWT_EXPIRES_IN = var.jwt_expires_in
  }

  cloudwatch_logs_retention_in_days = 14

  attach_policy_statements = true
  policy_statements = {
    dynamodb_query = {
      effect  = "Allow"
      actions = ["dynamodb:Query"]
      resources = [
        module.users_table.dynamodb_table_arn,
        "${module.users_table.dynamodb_table_arn}/index/${local.email_index_name}",
      ]
    }
  }
}
