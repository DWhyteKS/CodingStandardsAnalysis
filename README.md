# PowerShell Code Reviewer

## Overview
Automated PowerShell code review application that analyzes uploaded scripts against coding standards using Azure OpenAI. Provides detailed feedback on code quality, security, and best practices compliance.

**Key Features:**
- Upload .ps1, .psm1, .psd1 files for review (max 16MB)
- AI-powered analysis with detailed recommendations
- Enhanced analysis mode for production users
- Automated security and vulnerability scanning
- Drag-and-drop file upload support
- Real-time monitoring with Application Insights

## Prerequisites
- Python 3.11+
- Azure subscription
- Terraform
- Docker (for local development)
- Flask secret key for session management

## Quick Start
1. Visit the web application
2. Upload a PowerShell file (.ps1, .psm1, .psd1) - max 16MB
3. Receive detailed code review with recommendations
4. Check /health endpoint for system status

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with required variables
cat > .env << EOF
SECRET_KEY="your-secret-key"
storageConnectionString="your-storage-connection"
openAIEndpoint="your-openai-endpoint"
openAIKey="your-openai-key"
openAIDeploymentName="your-deployment-name"
EOF

# Run application
python app/app.py

# Or run with Docker
docker build -t powershell-reviewer .
docker run -p 5000:5000 --env-file .env powershell-reviewer

# Run tests
pytest -v

# Run security scan
bandit -r app
```

## Deployment

**Infrastructure**: Deployed using Terraform modules
- First deploy infrastructure: `terraform apply` in appropriate environment folder
- Remote state stored in Azure Storage
- Separate infrastructure for dev/prod environments

**CI/CD Pipeline**:
- Dev Environment: Triggers on `develop` branch push
- Prod Environment: Triggers on `main` branch push
- Container Registry: Azure Container Registry per environment
- Deployment: Azure App Service pulls container from registry

## Technology Stack
- **Backend**: Python Flask
- **Frontend**: HTML/CSS/JavaScript with drag-and-drop
- **AI Service**: Azure OpenAI
- **Infrastructure**: Terraform, Azure App Service (Docker containers)
- **CI/CD**: GitHub Actions
- **Monitoring**: Application Insights
- **Security**: Azure Key Vault (via Managed Identity), Trivy, Bandit

## File Requirements & Limitations
- **Supported extensions**: .ps1, .psm1, .psd1
- **Maximum file size**: 16MB
- **Encoding**: UTF-8
- **Input validation**: Werkzeug secure_filename()

## Monitoring & Troubleshooting

**Health Check**: `/health` endpoint returns application status and configuration

**Key Monitoring Queries (Application Insights):**

Recent Errors:
```kql
traces
| where severityLevel >= 3
| where timestamp > ago(1h)
| order by timestamp desc
| limit 20
```

File Upload Activity:
```kql
traces
| where message contains "file" or message contains "upload"
| where timestamp > ago(24h)
| order by timestamp desc
| limit 50
```

Feature Toggle Usage:
```kql
traces
| where message contains "analysis mode"
| where timestamp > ago(24h)
| summarize Count=count() by tostring(customDimensions.message)
| order by Count desc
```

Health Status:
```kql
traces
| where message contains "Health check"
| where timestamp > ago(6h)
| order by timestamp desc
| limit 10
```

## Architecture
System architecture includes:
- Docker containers running on Azure App Service
- Managed Identity for secure Key Vault access
- Application Insights middleware for comprehensive monitoring
- Terraform-managed infrastructure with remote state

See architecture diagrams for detailed system flow and CI/CD pipeline.