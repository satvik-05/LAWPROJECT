#!/bin/bash

# Pre-startup script for HF Spaces
# Downloads models once to avoid storage issues

echo "🚀 Pre-startup: Downloading required models..."

# Download spaCy model
python -m spacy download en_core_web_sm

echo "✅ Models downloaded"
echo "🔧 Starting application..."

# Start the Streamlit app (which will start backend internally)
streamlit run frontend/app.py --server.port=7860 --server.address=0.0.0.0
