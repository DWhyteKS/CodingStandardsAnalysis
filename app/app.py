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
from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
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
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configuration settings - try environment variables first, then defaults
# This allows the app to work locally and in Azure
storageConnectionString = os.environ.get('storageConnectionString', '')
openAIEndpoint = os.environ.get('openAIEndpoint', '')
openAIKey = os.environ.get('openAIKey', '')
openAIDeploymentName = os.environ.get('openAIDeploymentName', '')

# File upload settings
uploadFolder = 'uploads'
allowedFileTypes = {'ps1', 'psm1', 'psd1'}  # PowerShell file extensions
maxFileSize = 16 * 1024 * 1024  # 16MB max file size

# Set upload folder and file size limit
app.config['uploadFolder'] = uploadFolder
app.config['maxFileSize'] = maxFileSize

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
        
        # Prompt for AI service
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
    """
    Handle file upload and code review.
    This route processes the uploaded PowerShell file and returns review results.
    
    Flow:
    1. Check if file was uploaded
    2. Validate file type
    3. Save file temporarily
    4. Get coding standards
    5. Send for review
    6. Display results
    
    Returns:
        Rendered HTML template with review results or error messages
    """
    logger.info("File upload request received")
    
    # Check if the post request has the file part
    if 'file' not in request.files:
        flash('No file selected for upload', 'error')
        logger.warning("No file in upload request")
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    # Check if user actually selected a file
    if file.filename == '':
        flash('No file selected for upload', 'error')
        logger.warning("Empty filename in upload request")
        return redirect(url_for('index'))
    
    # Check if file type is allowed
    if not allowedFile(file.filename):
        flash('Invalid file type. Please upload PowerShell files (.ps1, .psm1, .psd1)', 'error')
        logger.warning(f"Invalid file type uploaded: {file.filename}")
        return redirect(url_for('index'))
    
    try:
        # Read the file content
        file_content = file.read().decode('utf-8')
        logger.info(f"Successfully read file: {file.filename}")
        
        # Get coding standards (from Azure Storage or local file)
        standards = getCodingStandards()
        
        # Send code for review (using Azure OpenAI or mock review)
        review_results = review_powershell_code(file_content, standards)
        
        # Render results page with the review
        return render_template('upload.html', 
                             review_results=review_results,
                             filename=secure_filename(file.filename),
                             success=True)
        
    except UnicodeDecodeError:
        flash('Error reading file. Please ensure it is a valid text file.', 'error')
        logger.error(f"Unicode decode error for file: {file.filename}")
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        logger.error(f"Error processing upload: {str(e)}")
        return redirect(url_for('index'))


@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring.
    Used by Azure App Service and monitoring tools to check if app is running.
    
    Returns:
        JSON response with application status
    """
    return {
        'status': 'healthy',
        'has_openai_config': bool(openAIEndpoint and openAIKey),
        'has_storage_config': bool(storageConnectionString)
    }


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
    
    # Run in debug mode locally, production mode in Azure
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Flask app on port {port}, debug mode: {debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)