#!/bin/bash

echo "🚀 Starting AI Interview Assistant..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

# Function to start backend
start_backend() {
    echo "📦 Starting FastAPI backend..."
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo "🔧 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "📥 Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo "⚠️  No .env file found. Please create one based on .env.example"
        echo "   You need to add your OPENROUTER_API_KEY"
        cp .env.example .env
        echo "   Edit backend/.env with your API key before starting the server."
        read -p "Press Enter once you've configured the .env file..."
    fi
    
    # Start the backend server
    echo "🚀 Starting FastAPI server on http://localhost:8000..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "⚛️  Starting React frontend..."
    cd frontend
    
    # Install dependencies
    echo "📥 Installing Node.js dependencies..."
    npm install
    
    # Start the frontend server
    echo "🚀 Starting React server on http://localhost:5173..."
    npm run dev &
    FRONTEND_PID=$!
    cd ..
}

# Start both services
start_backend
sleep 5  # Give backend time to start
start_frontend

echo ""
echo "✅ AI Interview Assistant is starting up!"
echo "🌐 Frontend: http://localhost:5173"
echo "🔗 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup SIGINT

# Wait for user to stop
wait