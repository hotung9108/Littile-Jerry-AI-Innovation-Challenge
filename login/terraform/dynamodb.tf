locals {
  email_index_name = "EmailIndex"
}

module "users_table" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  version = "~> 5.0"

  name     = "${var.project_name}-users-${var.environment}"
  hash_key = "id"

  attributes = [
    {
      name = "id"
      type = "S"
    },
    {
      name = "email"
      type = "S"
    },
  ]

  global_secondary_indexes = [
    {
      name            = local.email_index_name
      hash_key        = "email"
      projection_type = "ALL"
    },
  ]
}
