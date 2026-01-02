#!/bin/bash

# 🚂 Italian Train Trip Planner - Quick Start Script
# This script starts both the backend server and opens the frontend

echo "🚂 Italian Train Trip Planner - Starting..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv .venv"
    echo "Then: source .venv/bin/activate"
    echo "And: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Check if required packages are installed
echo "📦 Checking dependencies..."
python -c "import flask, flask_cors" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing dependencies. Installing..."
    pip install flask flask-cors
fi

# Start backend server in background
echo "🔧 Starting backend server on port 5001..."
python "$SCRIPT_DIR/frontend/backend_server.py" &
BACKEND_PID=$!

# Wait for backend to be ready
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "✅ Backend server running (PID: $BACKEND_PID)"
    echo "📍 API: http://localhost:5001"
else
    echo "❌ Backend failed to start!"
    exit 1
fi

# Open frontend in default browser
echo "🌐 Opening frontend..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$SCRIPT_DIR/frontend/index.html"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$SCRIPT_DIR/frontend/index.html"
else
    echo "Please open: $SCRIPT_DIR/frontend/index.html"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ System Ready!"
echo ""
echo "📝 Frontend opened in your browser"
echo "🔧 Backend API: http://localhost:5001"
echo "📚 Health check: http://localhost:5001/api/health"
echo ""
echo "Press Ctrl+C to stop the backend server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Keep script running and handle Ctrl+C
trap "echo ''; echo '🛑 Stopping backend server...'; kill $BACKEND_PID 2>/dev/null; echo '✅ Server stopped'; exit 0" INT

# Wait for backend process
wait $BACKEND_PID
