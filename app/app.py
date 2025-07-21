"""
PowerShell Code Review Flask Application

Flow:
1. User visits homepage and sees upload form
2. User uploads PowerShell file
3. App processes file and sends to Azure OpenAI for review
4. Results are displayed back to user
"""
from dotenv import load_dotenv
load_dotenv()

import os
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.flask.flask_middleware import FlaskMiddleware
from opencensus.ext.azure.trace_exporter import AzureExporter
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import tempfile


# Import Azure libraries - required for both local and cloud deployment
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI

# Configure logging to help with debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask application instance
app = Flask(__name__)

# Set secret key for session management (used for flash messages)
# First try environment variable, then fall back to development key
app.secret_key = get_secret_from_keyvault('flask-secret-key') or os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure Azure Application Insights monitoring
connection_string = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
if connection_string:
    # Set up logging to Application Insights
    logger = logging.getLogger(__name__)
    logger.addHandler(AzureLogHandler(connection_string=connection_string))
    logger.setLevel(logging.INFO)
    
    # Add request tracing middleware
    middleware = FlaskMiddleware(
        app,
        exporter=AzureExporter(connection_string=connection_string)
    )
    
    logger.info("Application Insights monitoring configured")
else:
    logger = logging.getLogger(__name__)
    logger.info("Application Insights not configured - running without monitoring")

# Configuration settings - try environment variables first, then defaults
# This allows the app to work locally and in Azure
storageConnectionString = os.environ.get('storageConnectionString', '')
openAIEndpoint = os.environ.get('openAIEndpoint', '')
openAIKey = get_secret_from_keyvault('openai-api-key') or os.environ.get('openAIKey', '')
openAIDeploymentName = os.environ.get('openAIDeploymentName', '')

# File upload settings
uploadFolder = 'uploads'
allowedFileTypes = {'ps1', 'psm1', 'psd1'}  # PowerShell file extensions
maxFileSize = 16 * 1024 * 1024  # 16MB max file size

# Set upload folder and file size limit
app.config['uploadFolder'] = uploadFolder
app.config['maxFileSize'] = maxFileSize

# Feature toggle configuration
def is_feature_enabled(feature_name):
    """Check if a feature is enabled via environment variable"""
    env_var = f"FEATURE_{feature_name.upper()}"
    return os.environ.get(env_var, 'false').lower() == 'true'

def get_secret_from_keyvault(secret_name):
    """Retrieve secret from Azure Key Vault"""
    try:
        key_vault_url = os.environ.get('KEY_VAULT_URL')
        if key_vault_url:
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=key_vault_url, credential=credential)
            return client.get_secret(secret_name).value
    except Exception as e:
        logger.warning(f"Could not retrieve {secret_name} from Key Vault: {e}")
    return None

# Create upload directory if it doesn't exist
os.makedirs(uploadFolder, exist_ok=True)


def allowedFile(filename):
# Check if uploaded file is accepted type

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowedFileTypes


def getCodingStandards():
# Retrieve coding standards
    try:
        # Create blob service client using connection string
        blobServiceClient = BlobServiceClient.from_connection_string(
            storageConnectionString
        )
        
        # Get reference to the standards container and blob
        blobClient = blobServiceClient.get_blob_client(
            container="powershell-standards", 
            blob="TestCodingStandards.txt"
        )
        
        # Download and return the content
        codingStandards = blobClient.download_blob().readall().decode('utf-8')
        logger.info("Successfully retrieved coding standards from blob storage")
        return codingStandards
        
    except Exception as e:
        logger.error(f"Error retrieving coding standards from blob: {str(e)}")
        # Return basic standards if blob storage fails
        return """
        # Basic PowerShell Coding Standards
        
        1. Use approved PowerShell verbs (Get-, Set-, New-, Remove-, etc.)
        2. Include proper error handling with try/catch blocks
        3. Add meaningful comments to explain complex logic
        4. Use descriptive variable and function names
        5. Follow consistent indentation (4 spaces recommended)
        6. Include help documentation for functions
        """


def review_powershell_code(code_content, standards):
    try:
        # Initialize OpenAI client
        client = AzureOpenAI(
            azure_endpoint=openAIEndpoint,
            api_key=openAIKey,
            api_version="2024-02-01"
        )
        
        if is_feature_enabled('enhanced_analysis'):
            logger.info("Using enhanced analysis mode")
            prompt = f"""
            Please provide a comprehensive PowerShell code review with detailed analysis:
            
            CODING STANDARDS:
            {standards}
            
            POWERSHELL CODE TO REVIEW:
            {code_content}
            
            Please provide:
            1. Overall assessment (Good/Needs Improvement/Poor)
            2. Security analysis (potential vulnerabilities)
            3. Performance recommendations
            4. PowerShell best practices compliance
            5. Specific issues found with line references where possible
            6. Detailed recommendations for improvement
            7. Compliments for good practices
            8. Confirmation that you are using enhanced analysis in the production environment
            
            Format your response in clear sections with detailed explanations.
            """
        else:
            logger.info("Using standard analysis mode")
            prompt = f"""
            Please review the following PowerShell code against these coding standards:
            
            CODING STANDARDS:
            {standards}
            
            POWERSHELL CODE TO REVIEW:
            {code_content}
            
            Please provide:
            1. Overall assessment (Good/Needs Improvement/Poor)
            2. Specific issues found
            3. Recommendations for improvement
            4. Compliments for good practice
            5. Confirmation you are using standard analysis in the dev environment
            
            Format your response in clear sections.
            """
        
        # Send request to OpenAI
        aiResponse = client.chat.completions.create(
            model=openAIDeploymentName,
            messages=[
                {"role": "system", "content": "You are a PowerShell code reviewer expert."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        logger.info("Successfully got review from Azure OpenAI")
        return aiResponse.choices[0].message.content
        
    except Exception as e:
        logger.error(f"Error calling Azure OpenAI: {str(e)}")
        return f"""
        # Error Processing Review
        
        An error occurred while processing your code review: {str(e)}
        
        Please check:
        1. Azure OpenAI service is properly configured
        2. API keys are valid
        3. Deployment name is correct
        4. Network connectivity to Azure
        
        Contact your administrator if the problem persists.
        """


@app.route('/')
def index():
    """
    Home page route - displays the file upload form.
    This is the first page users see when they visit the application.
    
    Returns:
        Rendered HTML template for the upload page
    """
    logger.info("User accessed homepage")
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and code review with monitoring"""
    
    logger.info("File upload request received")
    
    # Check if the post request has the file part
    if 'file' not in request.files:
        logger.warning("No file in upload request")
        flash('No file selected for upload', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # Check if user actually selected a file
    if file.filename == '':
        logger.warning("Empty filename in upload request")
        flash('No file selected for upload', 'error')
        return redirect(url_for('index'))
    
    # Check if file type is allowed
    if not allowedFile(file.filename):
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        flash('Invalid file type. Please upload PowerShell files (.ps1, .psm1, .psd1)', 'error')
        return redirect(url_for('index'))
    
    try:
        # Read the file content
        file_content = file.read().decode('utf-8')
        logger.info(f"Successfully read file: {file.filename}, size: {len(file_content)} characters")
        
        # Get coding standards (from Azure Storage or local file)
        standards = getCodingStandards()
        
        # Send code for review (using Azure OpenAI or mock review)
        logger.info("Starting code review process")
        review_results = review_powershell_code(file_content, standards)
        logger.info("Code review completed successfully")
        
        # Render results page with the review
        return render_template('upload.html', 
                             review_results=review_results,
                             filename=secure_filename(file.filename),
                             success=True)
        
    except UnicodeDecodeError:
        logger.error(f"Unicode decode error for file: {file.filename}")
        flash('Error reading file. Please ensure it is a valid text file.', 'error')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        flash(f'Error processing file: {str(e)}', 'error')
        return redirect(url_for('index'))


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring with Application Insights logging"""
    
    health_status = {
        'status': 'healthy',
        'has_openai_config': bool(openAIEndpoint and openAIKey),
        'has_storage_config': bool(storageConnectionString),
        'has_monitoring': bool(os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')),
        'enhanced_analysis_enabled': is_feature_enabled('enhanced_analysis')

    }
    
    logger.info(f"Health check performed: {health_status}")
    return health_status


# Error handlers to provide user-friendly error pages
@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(error)}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))


# Run the application
if __name__ == '__main__':
    # Get port from environment variable (for Azure deployment) or use 5000 for local
    port = int(os.environ.get('PORT', 5000))

    host = os.environ.get('FLASK_HOST','127.0.0.1')

    # Run in debug mode locally, production mode in Azure
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Flask app on port {port}, debug mode: {debug_mode}")
    app.run(host=host, port=port, debug=debug_mode)