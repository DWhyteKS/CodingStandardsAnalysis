FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY app/ ./

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]