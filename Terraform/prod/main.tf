module "powershell_reviewer" {
  source = "../../modules"
  
  environment              = "prod"
  resource_group_name      = "rg-powershell-reviewer-prod"
  app_service_name         = "app-powershell-reviewer-prod"
  storage_account_name     = "stpwshreviewerprod"
  acr_name                 = "acrpowershellreviewerprod"
  key_vault_name           = "kv-powershell-reviewer-prod"
  openai_name              = "openai-powershell-reviewer-prod"
  app_service_plan_name    = "asp-powershell-reviewer-prod"
  flask_secret_key         = var.flask_secret_key
}

variable "flask_secret_key" {
  description = "Secret key for Flask session management"
  type        = string
  sensitive   = true
}
