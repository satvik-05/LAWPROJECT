#!/bin/bash

# Pre-start script for Hugging Face Spaces
# This runs before the Streamlit app starts

echo "🚀 IPC Legal Assistant - Pre-start Setup"

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
    echo "📊 Ingesting IPC dataset (first time setup)..."
    python scripts/ingest_ipc.py || echo "⚠️ Warning: Data ingestion had issues, will retry at runtime"
else
    echo "✅ Vector store already exists"
fi

# Start FastAPI backend in the background
echo "🔧 Starting FastAPI backend..."
uvicorn backend.app.main:app --host 0.0.0.0 --port 7860 &

# Wait a moment for backend to start
sleep 3

echo "✅ Pre-start complete! Backend should be running on port 7860"
echo "📱 Streamlit will start on port 8501"

# The Streamlit app will start automatically after this script completes
