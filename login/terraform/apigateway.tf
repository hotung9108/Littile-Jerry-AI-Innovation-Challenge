module "api_gateway_login" {
  source  = "terraform-aws-modules/apigateway-v2/aws"
  version = "~> 6.0"

  name          = "${var.project_name}-${var.environment}"
  protocol_type = "HTTP"

  # Không dùng custom domain, chỉ dùng endpoint mặc định của API Gateway.
  create_domain_name = false

  routes = {
    "POST /login" = {
      integration = {
        uri                    = module.lambda_login.lambda_function_invoke_arn
        payload_format_version = "2.0"
        type                   = "AWS_PROXY"
      }
    }
  }
}

resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_login.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${module.api_gateway_login.api_execution_arn}/*/*"
}
