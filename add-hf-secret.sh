#!/bin/bash

# Add secrets to Hugging Face Space
# This script uses the Hugging Face API to add secrets

echo "🔐 Add Secrets to Hugging Face Space"
echo "====================================="
echo ""

# Prompt for credentials
read -p "Enter your Hugging Face username: " HF_USERNAME
read -p "Enter your Space name: " SPACE_NAME
echo ""
echo "⚠️  Your token will be hidden as you type"
read -s -p "Enter your Hugging Face access token: " HF_TOKEN
echo ""
echo ""

# Add USE_LOCAL_EMBEDDINGS secret
echo "Adding USE_LOCAL_EMBEDDINGS=true secret..."
curl -X POST \
  "https://huggingface.co/api/spaces/${HF_USERNAME}/${SPACE_NAME}/secrets" \
  -H "Authorization: Bearer ${HF_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"key": "USE_LOCAL_EMBEDDINGS", "value": "true", "description": "Use local sentence-transformers instead of Gemini API"}'

echo ""
echo ""
echo "✅ Secret added successfully!"
echo ""
echo "⏳ Your Space will rebuild automatically (2-3 minutes)"
echo "🔗 Check status at: https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}"
echo ""
echo "💡 Optional: Add API keys for LLM functionality"
echo "   You can add GEMINI_API_KEY or OPENAI_API_KEY through the web UI at:"
echo "   https://huggingface.co/spaces/${HF_USERNAME}/${SPACE_NAME}/settings"
