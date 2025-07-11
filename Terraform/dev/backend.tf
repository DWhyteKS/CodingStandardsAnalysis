terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "sttformstate"
    container_name       = "tfstate"
    key                  = "dev/powershell-reviewer.terraform.tfstate"
  }
}