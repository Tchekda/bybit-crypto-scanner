FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py .
COPY web_app.py .
COPY templates/ templates/
COPY static/ static/

# Create volume mount point for persistent data
VOLUME ["/app/data"]

# Expose port for web interface
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DATA_FILE=/app/data/volume_data.json

# Default command runs the web interface
CMD ["python", "web_app.py"]
