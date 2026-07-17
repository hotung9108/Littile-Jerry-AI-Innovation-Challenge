variable "aws_region" {
  description = "AWS region để deploy các resource"
  type        = string
  default     = "ap-southeast-1"
}

variable "project_name" {
  description = "Tiền tố đặt tên cho các resource"
  type        = string
  default     = "login-api"
}

variable "environment" {
  description = "Tên môi trường (dev, staging, prod...)"
  type        = string
  default     = "dev"
}

variable "jwt_secret" {
  description = "Secret dùng để ký JWT"
  type        = string
  sensitive   = true
}

variable "jwt_expires_in" {
  description = "Thời hạn access token (vd: 1h, 15m)"
  type        = string
  default     = "1h"
}
