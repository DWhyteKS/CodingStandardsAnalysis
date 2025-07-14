terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state-prod"
    storage_account_name = "sttformstateprod" 
    container_name       = "tfstate"
    key                  = "prod/powershell-reviewer.terraform.tfstate"
  }
}