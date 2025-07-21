# Configure the Azure Provider
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {}
}

# Create a resource group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "PowerShell-Code-Reviewer"
  }
}

# Create a storage account
resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    Environment = var.environment
    Project     = "PowerShell-Code-Reviewer"
  }
}

# Create a blob container for PowerShell standards
resource "azurerm_storage_container" "standards" {
  name                  = "powershell-standards"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Create Azure Container Registry
resource "azurerm_container_registry" "main" {
  name                = var.acr_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = {
    Environment = var.environment
    Project     = "PowerShell-Code-Reviewer"
  }
}

# Create Key Vault
resource "azurerm_key_vault" "main" {
  name                        = var.key_vault_name
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false

  sku_name = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get",
    ]

    secret_permissions = [
      "Get",
      "Set",
      "List",
      "Delete",
    ]

    storage_permissions = [
      "Get",
    ]
  }

  tags = {
    Environment = var.environment
    Project     = "PowerShell-Code-Reviewer"
  }
}

# Create Application Insights for monitoring

# resource "azurerm_application_insights" "main" {
#   name                = "ai-${var.app_service_name}"
#   location            = azurerm_resource_group.main.location
#   resource_group_name = azurerm_resource_group.main.name
#   application_type    = "web"
#   retention_in_days   = 90

#   tags = {
#     Environment = var.environment
#     Project     = "PowerShell-Code-Reviewer"
#   }
# }

# Get current client configuration
data "azurerm_client_config" "current" {}

# Create Azure OpenAI service
resource "azurerm_cognitive_account" "openai" {
  name                = var.openai_name
  location            = var.openai_location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = "S0"

  tags = {
    Environment = var.environment
    Project     = "PowerShell-Code-Reviewer"
  }
}

# Create App Service Plan
resource "azurerm_service_plan" "main" {
  name                = var.app_service_plan_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"

  tags = {
    Environment = var.environment
    Project     = "PowerShell-Code-Reviewer"
  }
}

# Create App Service
resource "azurerm_linux_web_app" "main" {
  name                = var.app_service_name
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_service_plan.main.location
  service_plan_id     = azurerm_service_plan.main.id

  identity {
    type = "SystemAssigned"
  }


  site_config {
    application_stack {
      docker_image     = "${azurerm_container_registry.main.login_server}/powershell-code-reviewer"
      docker_image_tag = "latest"
    }
  }

  app_settings = {
    "DOCKER_REGISTRY_SERVER_URL"            = "https://${azurerm_container_registry.main.login_server}"
    "DOCKER_REGISTRY_SERVER_USERNAME"       = azurerm_container_registry.main.admin_username
    "DOCKER_REGISTRY_SERVER_PASSWORD"       = azurerm_container_registry.main.admin_password
    "storageConnectionString"               = azurerm_storage_account.main.primary_connection_string
    "openAIEndpoint"                        = azurerm_cognitive_account.openai.endpoint
    "openAIKey"                             = azurerm_cognitive_account.openai.primary_access_key
    "openAIDeploymentName"                  = var.openai_deployment_name
    "KEY_VAULT_URL"                         = azurerm_key_vault.main.vault_uri
    "FLASK_ENV"                             = var.environment == "prod" ? "production" : "development"
    "FLASK_HOST"                            = "0.0.0.0"
    "SECRET_KEY"                            = var.flask_secret_key
    # "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.main.connection_string
    # "APPINSIGHTS_INSTRUMENTATION_KEY"       = azurerm_application_insights.main.instrumentation_key
    "FEATURE_ENHANCED_ANALYSIS"             = var.environment == "prod" ? "true" : "false"
  }

  tags = {
    Environment = var.environment
    Project     = "PowerShell-Code-Reviewer"
  }
}

# Store OpenAI key in Key Vault
resource "azurerm_key_vault_secret" "openai_key" {
  name         = "openai-api-key"
  value        = azurerm_cognitive_account.openai.primary_access_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}

resource "azurerm_key_vault_access_policy" "app_service" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = azurerm_linux_web_app.main.identity[0].principal_id

  secret_permissions = [
    "Get",
    "List"
  ]

  depends_on = [azurerm_linux_web_app.main]
}

resource "azurerm_key_vault_secret" "flask_secret" {
  name         = "flask-secret-key"
  value        = var.flask_secret_key
  key_vault_id = azurerm_key_vault.main.id

  depends_on = [azurerm_key_vault.main]
}