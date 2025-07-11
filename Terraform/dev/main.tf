module "powershell_reviewer" {
  source = "../../modules"
  
  environment              = "dev"
  resource_group_name      = "rg-powershell-reviewer-dev"
  app_service_name         = "app-powershell-reviewer-dev"
  storage_account_name     = "stpwshreviewerdev"
  acr_name                = "acrpowershellreviewerdev"
  key_vault_name          = "kv-powershell-reviewer-dev"
  openai_name             = "openai-powershell-reviewer-dev"
  app_service_plan_name   = "asp-powershell-reviewer-dev"
  flask_secret_key        = var.flask_secret_key
}