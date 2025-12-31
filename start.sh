#!/bin/bash

# Check if conda environment 'cadet' is activated
if [ "$CONDA_DEFAULT_ENV" != "cadet" ]; then
    echo "Error: conda environment 'cadet' is not activated."
    echo "Please run: conda activate cadet"
    exit 1
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

wait
