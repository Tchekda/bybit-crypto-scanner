#!/usr/bin/env bash
# Startup script for Bybit Volume Scanner Web Interface

cd "$(dirname "$0")"

echo "Starting Bybit Volume Scanner Web Interface..."
echo "=============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python -m venv venv
fi

# Install/update dependencies
echo "Installing dependencies..."
venv/bin/pip install -q -r requirements.txt

echo ""
echo "Starting web server..."
echo "Access the dashboard at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the web app
venv/bin/python web_app.py
