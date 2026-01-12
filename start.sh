#!/bin/bash

# Parse command line arguments
RESET_FLAG=false
if [ "$1" == "--reset" ]; then
    RESET_FLAG=true
fi

# Recommend using virtual environment
if [ -z "$CONDA_DEFAULT_ENV" ] && [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected."
    echo "It's recommended to activate a virtual environment first:"
    echo "  • For venv: source venv/bin/activate"
    echo "  • For conda: conda activate cadet"
    echo ""
fi

# Check if data pipeline setup is needed
SCHEMA_FILE="src/config/schema_info.json"
SETUP_NEEDED=false

if [ "$RESET_FLAG" = true ]; then
    echo ""
    echo "========================================"
    echo "RESETTING DATABASE AND PIPELINE"
    echo "========================================"
    echo ""
    python src/reset_db.py || exit 1
    SETUP_NEEDED=true
elif [ ! -f "$SCHEMA_FILE" ]; then
    echo ""
    echo "========================================"
    echo "FIRST TIME SETUP DETECTED"
    echo "========================================"
    echo ""
    echo "Schema file not found. Running data pipeline setup..."
    echo ""
    SETUP_NEEDED=true
fi

# Run data pipeline setup if needed
if [ "$SETUP_NEEDED" = true ]; then
    python src/setup.py || exit 1
    echo ""
    echo "Pipeline setup completed. Starting servers..."
    echo ""
fi

# Cleanup function to stop both servers
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $LANGGRAPH_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM

echo "Starting LangGraph server..."
langgraph dev &
LANGGRAPH_PID=$!

echo "Waiting for LangGraph to initialize..."
sleep 3

echo "Starting frontend..."
cd frontend && pnpm dev &
FRONTEND_PID=$!

echo ""
echo "========================================"
echo "Services started:"
echo "  LangGraph: http://localhost:2024"
echo "  Frontend:  http://localhost:3000"
echo "========================================"
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for frontend to be ready, then open browser
echo "Waiting for frontend to start..."
sleep 5

# Open browser (cross-platform)
URL="http://localhost:3000"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open "$URL"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open "$URL" 2>/dev/null || echo "Could not open browser automatically"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows Git Bash
    start "$URL"
else
    echo "Please open $URL in your browser"
fi

wait
