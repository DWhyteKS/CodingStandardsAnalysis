variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "rg-powershell-reviewer"
}

variable "location" {
  description = "The Azure Region in which all resources should be created"
  type        = string
  default     = "UK South"
}

variable "environment" {
  description = "Environment name (dev, prod, etc.)"
  type        = string
  default     = "dev"
}

variable "storage_account_name" {
  description = "Name of the storage account"
  type        = string
  default     = "stpowershellreviewer"
}

variable "acr_name" {
  description = "Name of the Azure Container Registry"
  type        = string
  default     = "acrpowershellreviewer"
}

variable "key_vault_name" {
  description = "Name of the Key Vault"
  type        = string
  default     = "kv-powershell-reviewer"
}

variable "openai_name" {
  description = "Name of the Azure OpenAI service"
  type        = string
  default     = "openai-powershell-reviewer"
}

variable "openai_location" {
  description = "Location for Azure OpenAI service"
  type        = string
  default     = "UK South"
}

variable "app_service_plan_name" {
  description = "Name of the App Service Plan"
  type        = string
  default     = "asp-powershell-reviewer"
}

variable "app_service_name" {
  description = "Name of the App Service"
  type        = string
  default     = "app-powershell-reviewer"
}

variable "openai_deployment_name" {
  description = "Name of the Azure OpenAI deployment/model to use"
  type        = string
  default     = "gpt-4.1-nano"
}

variable "flask_secret_key" {
  description = "Secret key for Flask session management"
  type        = string
  sensitive   = true