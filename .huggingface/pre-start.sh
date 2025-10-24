#!/bin/bash

echo "🚀 Starting IPC Legal Assistant pre-build steps..."

# Download spaCy model
echo "📦 Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p vectorstore

# Run data ingestion
echo "📊 Ingesting IPC dataset..."
python scripts/ingest_ipc.py

echo "✅ Pre-build complete!"
