output "resource_group_name" {
  description = "Name of the created resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "storage_connection_string" {
  description = "Connection string for the storage account"
  value       = azurerm_storage_account.main.primary_connection_string
  sensitive   = true
}

output "container_registry_login_server" {
  description = "Login server for the container registry"
  value       = azurerm_container_registry.main.login_server
}

output "container_registry_username" {
  description = "Admin username for the container registry"
  value       = azurerm_container_registry.main.admin_username
  sensitive   = true
}

output "container_registry_password" {
  description = "Admin password for the container registry"
  value       = azurerm_container_registry.main.admin_password
  sensitive   = true
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "openai_endpoint" {
  description = "Endpoint for the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_api_key" {
  description = "API key for the Azure OpenAI service"
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}

output "app_service_url" {
  description = "URL of the deployed App Service"
  value       = "https://${azurerm_linux_web_app.main.default_hostname}"
}

output "application_insights_connection_string" {
  description = "Connection string for Application Insights"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}

output "application_insights_instrumentation_key" {
  description = "Instrumentation key for Application Insights"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "action_group_id" {
  description = "ID of the monitoring action group"
  value       = azurerm_monitor_action_group.main.id
}

output "key_vault_name_for_email" {
  description = "Key Vault name where you need to manually add the admin-email secret"
  value       = azurerm_key_vault.main.name
}
