#!/bin/bash

# Startup script for Hugging Face Spaces
echo "🚀 IPC Legal Assistant - Starting..."

# Download spaCy model if not already present
if ! python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
    echo "📦 Downloading spaCy English model..."
    python -m spacy download en_core_web_sm
else
    echo "✅ spaCy model already installed"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p vectorstore

# Check if vectorstore exists and has data
if [ ! -f "vectorstore/chroma.sqlite3" ]; then
    echo "📊 Ingesting IPC dataset..."
    python scripts/ingest_ipc.py || echo "⚠️ Warning: Data ingestion had issues"
else
    echo "✅ Vector store already exists"
fi

# Start FastAPI backend in the background
echo "🔧 Starting FastAPI backend on port 7860..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 7860 --workers 1 &

# Wait for backend to start
sleep 5

# Check if backend is running
if curl -s http://127.0.0.1:7860/health > /dev/null; then
    echo "✅ Backend is running!"
else
    echo "⚠️ Backend may not be ready yet..."
fi

echo "✅ Startup complete!"
