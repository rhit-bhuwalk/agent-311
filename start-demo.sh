#!/bin/bash
# Startup script for full live WhatsApp demo

echo "======================================"
echo "  SF 311 WhatsApp Bot - Live Demo"
echo "======================================"
echo ""

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ ERROR: .env.local file not found!"
    echo "Please create .env.local and add your API keys."
    exit 1
fi

# Check if GEMINI_API_KEY is set
if ! grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env.local; then
    echo "✅ Gemini API key is configured"
else
    echo "⚠️  WARNING: Please update GEMINI_API_KEY in .env.local"
    echo "Get your key from: https://aistudio.google.com/app/apikey"
fi

# Check if Twilio credentials are set
if grep -q "TWILIO_ACCOUNT_SID=your_twilio_account_sid_here" .env.local; then
    echo "⚠️  WARNING: Twilio credentials not configured (optional for basic demo)"
fi

echo ""
echo "Starting services..."
echo ""
echo "📊 Frontend:    http://localhost:3000"
echo "🐍 Backend API: http://localhost:3001"
echo "📝 API Docs:    http://localhost:3001/docs"
echo "🤖 Graffiti:    http://localhost:3002"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup EXIT INT TERM

# Activate virtual environment
source .venv/bin/activate

# Start graffiti automation service (port 3002)
echo "🤖 Starting graffiti automation service..."
cd graffiti-automation
npm start > ../logs/graffiti.log 2>&1 &
GRAFFITI_PID=$!
cd ..

# Start backend (port 3001)
echo "🐍 Starting backend server..."
python3 -m uvicorn server.main:app --reload --port 3001 > logs/backend.log 2>&1 &
BACKEND_PID=$!

# Start frontend (port 3000)
echo "📊 Starting frontend..."
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ All services started!"
echo ""
echo "Logs are being written to:"
echo "  - logs/frontend.log"
echo "  - logs/backend.log"
echo "  - logs/graffiti.log"
echo ""
echo "Waiting for services to initialize..."
sleep 5

# Open browser
echo "🌐 Opening browser..."
open http://localhost:3000

# Keep script running and show logs
echo ""
echo "Showing backend logs (Ctrl+C to stop all services):"
echo "========================================================"
tail -f logs/backend.log
